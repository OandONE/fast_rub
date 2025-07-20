from typing import Optional
import os
import json
from colorama import Fore
import time

class Start:
    def __init__(
        self: "fast_rub.Client",
        session_name: str,
        token: Optional[str] = None,
        user_agent: Optional[str] = None,
        time_out: int = 60,
        display_welcome=True,
    ):
        name = session_name + ".faru"
        self.token = token
        self.user_agent = user_agent
        self.time_out = time_out
        if os.path.isfile(name):
            with open(name, "r", encoding="utf-8") as file:
                fast_rub_session_data = json.load(file)
                self.token = fast_rub_session_data["token"]
                self.time_out = fast_rub_session_data["time_out"]
                self.user_agent = fast_rub_session_data["user_agent"]
        else:
            if token == None:
                token = input("Enter your token : ")
                while not token:
                    print(Fore.RED, "Enter the token valid !")
                    token = input("Enter your token : ")
            fast_rub_session_data = {
                "session_name": session_name,
                "token": token,
                "user_agent": user_agent,
                "time_out": time_out,
                "display_welcome": display_welcome,
            }
            with open(name, "w", encoding="utf-8") as file:
                json.dump(
                    fast_rub_session_data, file, ensure_ascii=False, indent=4
                )
            self.token = token
            self.time_out = time_out
            self.user_agent = user_agent

        if display_welcome:
            k = ""
            for text in "Welcome to fast_rub":
                k += text
                print(Fore.GREEN, f"""{k}""", end="\r")
                time.sleep(0.07)
            print(Fore.WHITE, "")