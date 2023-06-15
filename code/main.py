import sys
# import network
import uasyncio as asyncio
from machine import Pin


class Stepper:
    sequence = [[1, 0, 0, 0],
                [1, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 1],
                [0, 0, 0, 1],
                [1, 0, 0, 1]
                ]
    
    
    def __init__(self, p1, p2, p3, p4):
        self.state = 0
        self.step_angle = 375  # deg * 100
        self.min_delay = 8  # ms
        self.delay = 8 # ms
        self.pins = [Pin(p1, Pin.OUT),
                     Pin(p2, Pin.OUT),
                     Pin(p3, Pin.OUT),
                     Pin(p4, Pin.OUT)]
    
    def idle(self):
        for pin in self.pins:
            pin.off()
    
    def speed(self, s):
        self.delay = s * 1000 // self.step_angle
        
    def angle_to_steps(self, angle):
        return (angle * 100) // self.step_angle
    
    def step(self, reverse=False):
        increment = - 1 if reverse else 1
        self.state = (self.state + increment) % len(__class__.sequence)
        self.set_state(self.state)
    
    def set_state(self, state_number):
        for pin, state in zip(self.pins, __class__.sequence[state_number]):
            pin.value(state)
        
    async def turn_steps(self, steps):
        reverse = False
        if steps < 0:
            reverse = True
            steps = -steps
        for _ in range(steps):
            self.step(reverse)
            await asyncio.sleep_ms(self.delay)
    
    async def turn_angle(self, angle):
        await self.turn_steps(self.angle_to_steps(angle))


class Cylinder:
    def __init__(self, motor):
        self.current = 0
        self.one_step_angle = 36
        self.motor = motor
        self.ratio = 25  # ratio * 10
    
    async def show(self, number):
        diff1 = (number - self.current) % 10
        diff2 = (self.current - number) % 10
        
        diff = diff1
        if diff2 < diff1:
            diff = -diff2
        angle = diff * self.one_step_angle
        self.current = number
        await self.motor.turn_angle(angle * self.ratio // 10 * -1)
        
    def idle(self):
        self.motor.idle()
        
    def reset_state(self):
        self.current = 0
        
        
class Display:
    def __init__(self,  digit0, digit1, digit2):
        self.digit0 = Cylinder(digit0)
        self.digit1 = Cylinder(digit1)
        self.digit2 = Cylinder(digit2)
        self.state_file = "state.txt"
    
    async def show(self, number):
        await asyncio.gather(
            self.digit2.show((number // 100) % 10),
            self.digit1.show((number // 10) % 10),
            self.digit0.show(number % 10)
        )
        
    async def showf(self, number, decimal):
        await self.show(int(number * 10 ** decimal))
        
    async def countdown(self, number):
        await self.show(number)
        await asyncio.sleep_ms(1000)
        
        for i in range(number):
            await self.show(number - i - 1)
            await asyncio.sleep_ms(1000)
        
    def load_state(self):
        with open(self.state_file, "r") as file:
            state = file.readline().split(",")
            self.digit2.current = int(state[0])
            self.digit2.motor.state = int(state[1])
            self.digit1.current = int(state[2])
            self.digit1.motor.state = int(state[3])
            self.digit0.current = int(state[4])
            self.digit0.motor.state = int(state[5])
    
    def save_state(self):
        with open(self.state_file, "w") as file:
            file.write(f"{self.digit2.current},{self.digit2.motor.state}, {self.digit1.current},{self.digit1.motor.state},{self.digit0.current},{self.digit0.motor.state}")
            
    def reset_state(self):
        self.digit1.reset_state()
        self.digit0.reset_state()
        self.save_state()
    
    def idle(self):
        self.digit1.idle()
        self.digit0.idle()
        
    async def start(self):
        """
        Control interface commands
        
        SHOW (int)          - displays integer, truncates from left
        SHOWF (float) (n)   - displays float with (n) digits after floating point, truncates from left
        CONFIGURE           - start the configuration mode
        """
        reader = asyncio.StreamReader(sys.stdin)
        while True:
            command_raw = await reader.readline()
            #print(command_raw)
            command_parts = command_raw.decode().split()
            
            
            try:
                command = command_parts[0].upper()
            except IndexError:
                continue
            
            #print(command_parts)
            
            if command == "SHOW":
                try:
                    await self.show(int(command_parts[1]))
                except:
                    print("Value is not a number")
            elif command == "SHOWF":
                try:
                    await self.showf(float(command_parts[1]), int(command_parts[2]))
                except:
                    print("Value is not a number")
            elif command == "COUNTDOWN":
                try:
                    print(f"Countdown from {int(command_parts[1])}")
                    await self.countdown(int(command_parts[1]))
                except:
                    print("Value is not a number")
            elif command == "INFO":
                print(self)
            elif command == "SAVE":
                self.save_state()
                print("State saved")
            elif command == "SET":
                self.digit0.current = int(command_parts[1]) % 10
                self.digit1.current = (int(command_parts[1]) // 10) % 10
                self.digit2.current = (int(command_parts[1]) // 100) % 10
                print(self)
            elif command == "CONFIGURE":
                print("CONFIGURATION started")
                while True:
                    command = await reader.read(1)
                    #print(type(command), command)
                    if command == "1":
                        self.digit0.motor.step()
                    elif command == "2":
                        self.digit0.motor.step(reverse=True)
                    elif command == "3":
                        self.digit1.motor.step()
                    elif command == "4":
                        self.digit1.motor.step(reverse=True)
                    elif command == "5":
                        self.digit2.motor.step()
                    elif command == "6":
                        self.digit2.motor.step(reverse=True)
                    elif command == "s":
                        self.reset_state()
                        self.save_state()
                        print("Display configuration success")
                        break
                    await asyncio.sleep_ms(30)
                
    
    def __repr__(self):
        r = "Display\n"
        r += f"\tDisplayed number: {self.digit2.current}{self.digit1.current}{self.digit0.current}\n"
        r += f"\tMotor states: {self.digit2.motor.state}, {self.digit1.motor.state}, {self.digit0.motor.state}\n"
        return r


# async def connect(ssid, psk):
#     #Connect to WLAN
#     wlan = network.WLAN(network.STA_IF)
#     wlan.active(True)
#     wlan.connect(ssid, psk)
#     for _ in range(10):
#         if wlan.isconnected():
#             break
#         print('Waiting for connection...')
#         asyncio.sleep_ms(3000)
#     else:
#         print("Cannot connect to network. Resetting...")
#         machine.reset()
    
#     ip = wlan.ifconfig()[0]
#     print(f'Connected to {ssid} on {ip}')
#     return ip


async def main():
    try:
        display.load_state()
    except Exception as e:
        print(e)
    print(display)
    
    await display.start()

    
digit0 = Stepper(0, 1, 2, 3)
digit0.delay = 16
digit1 = Stepper(4, 5, 6, 7)
digit1.delay = 16
digit2 = Stepper(8, 9, 10, 11)
digit2.delay = 16
display = Display(digit0, digit1, digit2)


try:
    asyncio.run(main())
except:
    print("Exception occured. Saving state and exiting.")
    display.save_state()
    raise
    