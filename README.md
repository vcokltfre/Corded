# Corded

A lightweight, extensible client library for Discord bots

Example usage:
```py
from corded import CordedClient, GatewayEvent


bot = CordedClient("my_token", 32767)

@bot.on("message_create")
async def on_message_create(event: GatewayEvent) -> None:
    data = event.typed_data

    print(data["content"])

bot.start()
```
