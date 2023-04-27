import logging
import asyncio


async def main():
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Starting the machine learning inference")
    await asyncio.sleep(2)
    logging.info("Streaming Sucessful")
    await asyncio.sleep(20)

    logging.info("[GOAL] Processing Sucessful")

    # Block execution until the future is done
    await asyncio.sleep(9999999)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
