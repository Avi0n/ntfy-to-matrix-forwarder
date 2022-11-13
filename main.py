import logging
import asyncio
import yaml
from nio import AsyncClient
import requests
from markdown import markdown
import json


with open("config.yaml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.Loader)
    
logging.basicConfig(level=config["logging_level"])


async def send_message(message):
    client = AsyncClient(config["homeserver"], config["username"])

    await client.login(config["password"])
    await client.sync(timeout=15)

    # Format message as markdown if configured to do so
    if config["markdown_format"]:
        # Replace \n with \r for markdown compatibility
        message = message.replace("\n", "\r")

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
        logging.error(f"Matrix message content was: {content}")

    await client.close()
    return


async def main():
    ntfy_server = config["ntfy_server"]
    ntfy_topic = config["ntfy_topic"]
    resp = requests.get(f"https://{ntfy_server}/{ntfy_topic}/json", stream=True)
    logging.info(f"Listening to ntfy topic: {ntfy_topic}")

    for line in resp.iter_lines():
        if line:
            # Convert to JSON
            json_msg = json.loads(line)

            if "message" in json_msg:
                logging.info(f"Received message from ntfy: {json.dumps(json_msg, indent=4)}")
                logging.info("Sending message to matrix room...")
                await send_message(json_msg["message"])
            else:
                logging.debug(json.dumps(json_msg, indent=4))


if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
