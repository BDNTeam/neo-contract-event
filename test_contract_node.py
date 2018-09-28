"""
Example of running a NEO node and receiving notifications when events
of a specific smart contract happen.

Events include Runtime.Notify, Runtime.Log, Storage.*, Execution.Success
and several more. See the documentation here:

http://neo-python.readthedocs.io/en/latest/smartcontracts.html
"""
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep

from logzero import logger
from twisted.internet import reactor, task

from neo.contrib.smartcontract import SmartContract
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neo.Network.NodeLeader import NodeLeader
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings

import asyncio
import websockets
import json

# If you want the log messages to also be saved in a logfile, enable the
# next line. This configures a logfile with max 10 MB and 3 rotations:
# settings.set_logfile("/tmp/logfile.log", max_bytes=1e7, backup_count=3)

# Setup the smart contract instance
smart_contract = SmartContract("cfdff42a0fa99aeee31e2af5e140e0f9040b5d46")


# Register an event handler for Runtime.Notify events of the smart contract.
@smart_contract.on_notify
def sc_notify(event):
    logger.info("SmartContract Runtime.Notify event: %s", event)

    # Make sure that the event payload list has at least one element.
    if not isinstance(event.event_payload,
                      ContractParameter) or event.event_payload.Type != ContractParameterType.Array or not len(
        event.event_payload.Value):
        return

    # The event payload list has at least one element. As developer of the smart contract
    # you should know what data-type is in the bytes, and how to decode it. In this example,
    # it's just a string, so we decode it with utf-8:
    logger.info("- payload part 1: %s", event.event_payload.Value[0].Value.decode("utf-8"))
    logger.info("- payload part 2: %s", event.event_payload.Value[1].Value.decode("utf-8"))
    logger.info("- payload part 3: %d",
                int.from_bytes(event.event_payload.Value[2].Value, byteorder='little', signed=True))

    # pack msg and push to SDK user
    with ThreadPoolExecutor(max_workers=1) as executor:
        ret = json.dumps({'from': 'fromm'})
        executor.submit(notify_event_task, ret)


def log_block_height():
    """ Custom code run in a background thread. Prints the current block height.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        sleep(15)


async def notify_event(msg):
    if ws_conn_poll:
        await asyncio.wait([conn.send(msg) for conn in ws_conn_poll])


def notify_event_task(msg):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.get_event_loop().run_until_complete(notify_event(msg))


ws_conn_poll = set()


async def register(conn):
    ws_conn_poll.add(conn)


async def unregister(conn):
    ws_conn_poll.remove(conn)


async def handle_conn(conn, path):
    await register(conn)
    try:
        async for message in conn:
            print(message)

    finally:
        await unregister(conn)


def start_ws():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ws = websockets.serve(handle_conn, 'localhost', settings.SDK_WS_PORT)
    asyncio.get_event_loop().run_until_complete(ws)
    logger.info(f"SDK Websocket Server running at: {settings.SDK_WS_PORT}")
    asyncio.get_event_loop().run_forever()


def main():
    # Use TestNet
    settings.setup_privnet()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)
    NodeLeader.Instance().Start()

    # Disable smart contract events for external smart contracts
    settings.set_log_smart_contract_events(False)

    # Start a thread for logging block height
    d = threading.Thread(target=log_block_height)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    # Start a thread for websocket server
    d = threading.Thread(target=start_ws)
    d.setDaemon(True)
    d.start()

    # Run all the things (blocking call)
    logger.info("Everything setup and running. Waiting for events...")
    reactor.run()
    logger.info("Shutting down.")


if __name__ == "__main__":
    main()
