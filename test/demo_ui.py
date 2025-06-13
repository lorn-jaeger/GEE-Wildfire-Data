from ee_wildfire.UserInterface.UserInterface import ConsoleUI
from datetime import datetime
import time

start_date = datetime(year=2021, month=1, day=1)
end_date = datetime(year=2021, month=1, day=14)

ConsoleUI.clear_screen()

ConsoleUI.print("Generating geodata")
time.sleep(1)

ConsoleUI.print("Generating something else with yellow text.", color="yellow")
time.sleep(1)

ConsoleUI.print("Configuring something, its red maybe something went wrong?", color="red")
time.sleep(1)

ConsoleUI.add_bar(key="bar", total=100, desc="Generation progress")

for i in range(0,100):
    time.sleep(0.01)
    ConsoleUI.update_bar(key="bar")
    ConsoleUI.change_bar_desc(key="bar", desc=f"Generation progress ({i}%)")

ConsoleUI.print("User input is handled, with path completion!")
ConsoleUI.prompt_path()


ConsoleUI.print("There can also be multiple bars!")
time.sleep(1)

ConsoleUI.add_bar(key="bar", total=10, desc="Files downloaded, but with red bar!", color="red")
for i in range(0,10):
    ConsoleUI.add_bar(key="bar2", total=100, desc="Yellow Download progress", color="yellow")
    for j in range(0,100):
        # ConsoleUI.print(str(j))
        ConsoleUI.update_bar(key="bar2")
        ConsoleUI.change_bar_desc(key="bar2", desc=f"Yellow Download progress : {j}%")
        time.sleep(0.01)

    ConsoleUI.update_bar(key="bar")

ConsoleUI.clear_screen()

