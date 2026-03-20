from getpass import getpass

import telethon
from qrcode import QRCode

qr = QRCode()


def gen_qr(token: str):
    qr.clear()
    qr.add_data(token)
    qr.print_ascii()


async def auth(client: telethon.TelegramClient):
    qr_login = await client.qr_login()

    r = False
    while not r:
        gen_qr(qr_login.url)
        print(qr_login.url)
        try:
            r = await qr_login.wait(10)
        except telethon.errors.rpcerrorlist.SessionPasswordNeededError:
            password = getpass("Please, specify 2FA password: ")
            await client.sign_in(password=password)
            r = True
        except Exception:
            await qr_login.recreate()
    # me = await client.get_me()
