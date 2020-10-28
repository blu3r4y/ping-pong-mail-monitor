import base64
import pickle
import os.path

from config import config

from email.mime.text import MIMEText

from loguru import logger
from googleapiclient import errors
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


class Gmail:
    def __init__(self) -> None:
        self.service = None
        self.creds = self._authenticate()

    def submit_uuid(self, recipient, uuid):
        return self._send_mail(recipient, "#JKUOEHMAILMONITOR# {}".format(uuid)) is not None

    def receive_uuid(self, uuid):
        return self._search_mail('to:me "{}"'.format(uuid))

    def _authenticate(self):
        creds = None

        # check if we have some stored credentials
        if os.path.exists("../data/token.pickle"):
            with open("../data/token.pickle", "rb") as token:
                creds = pickle.load(token)

        # if there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "../data/credentials.json",
                    [
                        "https://www.googleapis.com/auth/gmail.readonly",
                        "https://www.googleapis.com/auth/gmail.send",
                    ],
                )
                creds = flow.run_local_server(port=0)

            # save the credentials for the next run
            with open("../data/token.pickle", "wb") as token:
                pickle.dump(creds, token)

        self.service = build("gmail", "v1", credentials=creds)

        logger.info("successfully authenticated with gmail")

        return creds

    def _send_mail(self, recipient, subject, body=""):
        mime = MIMEText(body)
        mime["to"] = recipient
        mime["from"] = config["from_address"]
        mime["subject"] = subject

        raw = {"raw": base64.urlsafe_b64encode(mime.as_string().encode()).decode()}

        message = self.service.users().messages().send(userId="me", body=raw).execute()
        logger.info(
            "sent mail with id {} and subject '{}' to '{}'".format(
                message["id"], subject, recipient
            )
        )
        return message

    def _search_mail(self, query):
        result = (
            self.service.users()
            .messages()
            .list(userId="me", maxResults=1, includeSpamTrash=True, q=query)
            .execute()
        )

        nresults = result["resultSizeEstimate"]
        logger.info("search for query '{}' yielded {} results".format(query, nresults))
        return nresults == 1