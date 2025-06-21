"""
    A helper module for processing events that are not related to communication with Telegram API
"""

import os
import logging


from src.classes.user import UserRecord

DIRECTORIES = ['logs', 'session', 'config', 'reports']


async def matchAdminsByNames(channelUsers: dict[int, UserRecord], potentialAdmins: list[str]) -> dict[UserRecord, str]:
    foundAdmins = {}
    for user in channelUsers.values():
        userName = user.full_name
        matchedCounter = 0
        tempArray = []
        for name in potentialAdmins:
            if name in userName:
                matchedCounter += 1
                tempArray.append(user)
        
        if matchedCounter == 1:
            foundAdmins[tempArray[0]] = '[bold red]admin[/]'
        elif matchedCounter >= 2:
            for i in tempArray:
                foundAdmins[tempArray[i]] = '[bold orange]probably admin[/]'
        elif matchedCounter > 5:
            continue
    
    return foundAdmins


def _prepareWorkspace():
    """
        Prepare workspace for the application.
        This function creates necessary directories if not found
    """
    for directory in DIRECTORIES:
        if not os.path.exists(f'./{directory}'):
            try:
                os.makedirs(f'./{directory}')
            except OSError as e:
                logging.error(f"Error creating directory {directory}: {e}")
                exit(1)
            logging.info(f"Created {directory} directory")
        else:
            logging.debug(f"{directory} directory already exists")