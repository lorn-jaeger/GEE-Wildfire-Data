from ee_wildfire.UserInterface import ConsoleUI
from datetime import datetime
import time

start_date = datetime(year=2021, month=1, day=1)
end_date = datetime(year=2021, month=1, day=14)


ConsoleUI.print("Generating geodata")
time.sleep(1)

ConsoleUI.print("Generating something else")
time.sleep(1)

ConsoleUI.add_bar("bar1",100,"bar 1 dudde")
time.sleep(1)

ConsoleUI.print("bar 1 is bruhh dude")
for i in range(0,100):
    ConsoleUI.update_bar("bar1")
    time.sleep(0.01)
    ConsoleUI.print(f"testing {i}")



