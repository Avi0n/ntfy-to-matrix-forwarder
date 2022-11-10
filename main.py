import logging
import asyncio
import yaml
from nio import AsyncClient
import requests
from markdown import markdown
import re


with open("config.yaml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.Loader)
    
logging.basicConfig(level=config["logging_level"])


async def send_message(message):
    client = AsyncClient(config["homeserver"], config["username"])

    await client.login(config["password"])
    await client.sync(timeout=15)

    # Format message as markdown if configured to do so
    if config["markdown_format"]:
        # Replace two or more spaces with return carriage
        message = re.sub(r"[ ]{2,}", "\r\r", message)

        content = {
            "msgtype": "m.text",
            "format": "org.matrix.custom.html",
            "body": message,
        }

        # Convert message content to markdown
        content["formatted_body"] = markdown(message)
    else:
        content = {
            "msgtype": "m.text",
            "body": message,
        }

    # Send message to the matrix room
    try:
        await client.room_send(
            room_id=config["matrix_room"],
            message_type="m.room.message",
            content=content,
            ignore_unverified_devices=True,
        )
        logging.info("Message sent successfully.")
    except Exception as e:
        logging.error(f"Exception while attempting to send message: {e}")
        logging.info(f"Matrix message content was: {content}")

    await client.close()
    return


async def main():
    ntfy_server = config["ntfy_server"]
    ntfy_topic = config["ntfy_topic"]
    resp = requests.get(f"https://{ntfy_server}/{ntfy_topic}/raw", stream=True)
    logging.info(f"Listening to ntfy topic: {ntfy_topic}")

    for line in resp.iter_lines():
        if line:
            logging.info(f"Received message from ntfy: {line.decode('utf-8')}")
            logging.info("Sending message to matrix room...")
            await send_message(line.decode("utf-8"))


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
