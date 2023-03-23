"""
Solution to the one-way tunnel
"""
import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value, Manager

SOUTH = 1
NORTH = 0

#################################################
def muestraDireccion(direccion: int) -> str:
        return 'S' if direccion else 'N'
#################################################

QUANTITY = { 'N': 5, 'S': 5, 'P': 5 }
TIME_CARS = 0.5  # a new car enters each 0.5s
TIME_PED  = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS       = (0.5, 2)
TIME_IN_BRIDGE_PEDESTRIAN = (10, 30)

class Monitor():
    def __init__(self):
        self.mutex = Lock()
        self.semaphoreA = Condition(self.mutex)
        #self.semaphoreN = Condition(self.mutex)
        #self.semaphoreS = Condition(self.mutex)
        #self.semaphoreP = Condition(self.mutex)
        self.manager    = Manager()
        self.enPuente   = self.manager.dict({ 'North': 0
                                            , 'South': 0
                                            , 'Pedes': 0 })
        self.stats      = self.manager.dict({ 'North': 0
                                            , 'South': 0
                                            , 'Pedes': 0 })
    def no_NS(self) -> bool:
        return self.enPuente['North'] == 0 and self.enPuente['South'] == 0

    def no_SP(self) -> bool:
        return self.enPuente['South'] == 0 and self.enPuente['Pedes'] == 0

    def no_NP(self) -> bool:
        return self.enPuente['Pedes'] == 0 and self.enPuente['North'] == 0

    def no_carsN(self) -> bool:
        return self.enPuente['North'] == 0

    def no_carsS(self) -> bool:
        return self.enPuente['South'] == 0

    def no_pedes(self) -> bool:
        return self.enPuente['Pedes'] == 0

    def wants_to_enter(self, direccion: int) -> None:
        self.mutex.acquire()
    
        if direccion == NORTH:
            self.semaphoreA.wait_for(self.no_SP)
            self.enPuente['North'] += 1

        elif direccion == SOUTH:
            self.semaphoreA.wait_for(self.no_NP)
            self.enPuente['South'] += 1

        else:
            self.semaphoreA.wait_for(self.no_NS)
            self.enPuente['Pedes'] += 1

        self.mutex.release()

    def leaves_tunnel(self, direccion: int) -> None:
        self.mutex.acquire()

        if direccion == NORTH:
            self.enPuente['North'] -= 1
            self.stats['North']    += 1
            if self.no_carsN():
                self.semaphoreA.notify_all()

        elif direccion == SOUTH:
            self.enPuente['South'] -= 1
            self.stats['South']    += 1
            if self.no_carsS():
                self.semaphoreA.notify_all()

        else:
            self.enPuente['Pedes'] -= 1
            self.stats['Pedes']    += 1
            if self.no_pedes():
                self.semaphoreA.notify_all()

        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: \nNorth: {self.stats["North"]}\nSouth: {self.stats["South"]}\nPedestrians: {self.stats["Pedes"]}'

def delay_car() -> None:
    time.sleep(1)
    pass
   
def delay_pedestrian() -> None:
    time.sleep(2)
    pass

def car(cid: int, direccion: int, monitor: Monitor) -> None:
    print(f"car {cid} direction {muestraDireccion(direccion)} created")
    time.sleep(6)
    print(f"car {cid} heading {muestraDireccion(direccion)} wants to enter.")
    monitor.wants_to_enter(direccion)
    print(f"car {cid} heading {muestraDireccion(direccion)} enters the bridge.")

    print(f"[Puente]: {monitor.enPuente}")
    delay_car()

    print(f"car {cid} heading {muestraDireccion(direccion)} leaving the bridge.")
    monitor.leaves_tunnel(direccion)
    print(f"car {cid} heading {muestraDireccion(direccion)} out of the bridge. \n{monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} created")
    time.sleep(6)
    print(f"pedestrian {pid} wants to enter.")
    monitor.wants_to_enter(-1)
    print(f"pedestrian {pid} enters the bridge.")

    print(f"[Puente]: {monitor.enPuente}")
    delay_pedestrian()

    print(f"pedestrian {pid} leaving the bridge.")
    monitor.leaves_tunnel(-1)
    print(f"pedestrian {pid} out of the bridge. \n{monitor}")

def gen_pedestrian(quantidade: int, monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(quantidade):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(cid: Value, quantidade: int, direccion: int, time_cars, monitor: Monitor) -> None:
    plst = []
    for _ in range(quantidade):
        cid.value += 1
        p = Process(target=car, args=(cid.value, direccion, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor   = Monitor()
    contador = Manager().Value('i', 0)

    gcars_north = Process(target=gen_cars, args=(contador, QUANTITY['N'], NORTH, TIME_CARS, monitor))
    gcars_south = Process(target=gen_cars, args=(contador, QUANTITY['S'], SOUTH, TIME_CARS, monitor))
    gped        = Process(target=gen_pedestrian, args=(QUANTITY['P'], monitor))

    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()


if __name__ == '__main__':
    main()