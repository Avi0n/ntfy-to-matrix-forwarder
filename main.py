import asyncio
import yaml
from nio import AsyncClient
import requests
from markdown import markdown
import re


with open("config.yaml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.Loader)


async def send_message(message):
    client = AsyncClient(config["homeserver"], config["username"])

    await client.login(config["password"])
    await client.sync(timeout=15)

    # Replace two or more spaces with return carriage
    message = re.sub(r"[ ]{2,}", "\r\r", message)

    content = {
        "msgtype": "m.text",
        "format": "org.matrix.custom.html",
        "body": message,
    }

    # Convert message content to markdown
    content["formatted_body"] = markdown(message)

    # Send formatted message
    try:
        await client.room_send(
            room_id=config["matrix_room"],
            message_type="m.room.message",
            content=content,
            ignore_unverified_devices=True,
        )
    except SendRetryError:
        logger.exception(f"Unable to send message response to {room_id}")

    await client.close()
    return


async def main():
    ntfy_topic = config["ntfy_topic"]
    resp = requests.get(f"https://ntfy.sh/{ntfy_topic}/raw", stream=True)
    for line in resp.iter_lines():
        if line:
            print(line.decode("utf-8"))
            print("Sending message to matrix room")
            await send_message(line.decode("utf-8"))


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
