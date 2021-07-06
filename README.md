# Corded

A lightweight, extensible client library for Discord bots

Example usage:
```py
from corded import CordedClient, GatewayEvent, Intents


bot = CordedClient("my_token", Intents.default())

@bot.on("message_create")
async def on_message_create(event: GatewayEvent) -> None:
    data = event.typed_data

    print(data["content"])

bot.start()
```
