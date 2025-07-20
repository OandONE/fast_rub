

class SetCommands:
    async def set_commands(self: "fast_rub.Client", bot_commands: list):
        """مثال bot_commands :
        [{
                    "command": "command1",
                    "description": "description1"
                },
                {
                    "command": "command2",
                    "description": "description2"
                }
        ]"""
        data = {"bot_commands": [bot_commands]}
        result = await self.send_request("setCommands", data, request_type="post")
        return result