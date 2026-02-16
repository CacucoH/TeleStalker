"""
A helper module for processing events that are not related to communication with Telegram API
"""

import logging
import os

from src.classes.user import UserRecord

DIRECTORIES = ["logs", "session", "config", "reports"]


async def matchAdminsByNames(
    channelUsers: dict[int, UserRecord], potentialAdmins: set[str]
) -> dict[int, UserRecord]:
    foundAdmins = {}
    user: UserRecord
    for adminName in potentialAdmins:
        matchedCounter = 0
        tempArray: list[UserRecord] = []
        for user in channelUsers.values():
            userName: str = user.first_name
            if adminName.lower() == userName.lower():
                matchedCounter += 1
                tempArray.append(user)

        # Too much candidates
        if matchedCounter > 2:
            continue

        for adm in tempArray:
            foundAdmins[adm.id] = adm

    return foundAdmins


def _prepareWorkspace():
    """
    Prepare workspace for the application.
    This function creates necessary directories if not found
    """
    for directory in DIRECTORIES:
        if not os.path.exists(f"./{directory}"):
            try:
                os.makedirs(f"./{directory}")
            except OSError as e:
                logging.error(f"Error creating directory {directory}: {e}")
                exit(1)
            logging.info(f"Created {directory} directory")
        else:
            logging.debug(f"{directory} directory already exists")
