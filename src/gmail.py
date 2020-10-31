import base64
import pickle
import os.path

from pprint import pprint
from typing import Optional
from email.mime.text import MIMEText

from dateutil import parser
from loguru import logger
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


class Gmail:
    def __init__(self, credentials_path: str, token_path: str, port: int) -> None:
        """
        Initialize the GMail API

        :param credentials_path: Path to the `credentials.json` for this endpoint
        :param token_path: Path to the stored auth token, i.e. `token.pickle`
        :param port: The port to be opened for the OAuth callback authentication flow
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.port = port

        self.service = None
        self.from_address = None
        self.creds = self._authenticate()

    def submit_uuid(self, recipient, uuid):
        """
        Send an UUID mail to the recipient and return the sent timestamp (epoch ms)

        :param recipient: Recipient mail address
        :param uuid: The UUID to be sent
        :return: The timestamp in epoch milliseconds when the mail was received on the server
        """
        message = self._send_mail(recipient, "#JKUOEHMAILMONITOR# {}".format(uuid))
        return int(self._get_mail(message["id"])["internalDate"])

    def receive_uuid(self, uuid) -> Optional[int]:
        """
        Search for the UUID mail and return the receive timestamp (epoch ms)

        :param uuid: UUID to search for in received mails
        :return: The timestamp in epoch milliseconds when the mail was received on the server
        """
        message_id = self._search_mail('to:me "{}"'.format(uuid))
        return self._get_header_time(self._get_mail(message_id)) if message_id is not None else None

    def _authenticate(self):
        """
        Perform the standard OAuth authentication flow for this app, which requires user interaction

        :return: A credentials object
        """
        creds = None

        # check if we have some stored credentials
        if os.path.exists(self.token_path):
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)

        # if there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path,
                    [
                        "https://www.googleapis.com/auth/gmail.modify",
                    ],
                )
                creds = flow.run_local_server(port=self.port)

            # save the credentials for the next run
            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)

        self.service = build("gmail", "v1", credentials=creds)
        self.from_address = self._get_username()

        logger.success("successfully authenticated with {}".format(self.from_address))

        return creds

    def _get_username(self):
        """
        Get the full mail address of the authenticated user
        https://developers.google.com/gmail/api/reference/rest/v1/users/getProfile

        :return: The email address
        """
        user = self.service.users().getProfile(userId="me").execute()
        return user["emailAddress"]

    def _send_mail(self, recipient: str, subject: str, body: str = "") -> None:
        """
        Send a mail to some recipient with a given subject and body
        https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send

        :param recipient: Recipient mail address
        :param subject: Subject of the mail
        :param body: Body text of the mail, defaults to ""
        :param delete: Deletes the mail after sending
        """
        mime = MIMEText(body)
        mime["to"] = recipient
        mime["from"] = self.from_address
        mime["subject"] = subject

        raw = {"raw": base64.urlsafe_b64encode(mime.as_string().encode()).decode()}

        message = self.service.users().messages().send(userId="me", body=raw).execute()

        logger.debug(
            "sent mail with id {} and subject '{}' to {}".format(message["id"], subject, recipient)
        )
        return message

    def _search_mail(self, query: str) -> Optional[str]:
        """
        Search for an email with the given query and return the message id
        https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list

        :param query: A query just like in the search bar of the gmail app
        :return: The message id of the first match or None if there are no matches
        """
        result = (
            self.service.users()
            .messages()
            .list(userId="me", maxResults=1, includeSpamTrash=True, q=query)
            .execute()
        )

        nresults = result["resultSizeEstimate"]
        logger.debug("search for query '{}' yielded {} results".format(query, nresults))

        return result["messages"][0]["id"] if nresults > 0 else None

    def _get_mail(self, message_id: str) -> dict:
        """
        Get the message object for a given id
        https://developers.google.com/gmail/api/reference/rest/v1/users.messages/get

        :param message_id: The message id to retrieve
        :return: A message resource (https://developers.google.com/gmail/api/reference/rest/v1/users.messages#resource:-message)
        """
        message = self.service.users().messages().get(userId="me", id=message_id).execute()
        return message

    @staticmethod
    def _get_header_time(message):
        """
        Extract the epoch timestamp in ms from the 'Received' header of this mail.
        If this fails, the 'internalDate' is returned instead.

        :param message: The Message object from the GMail API
        :return: The epoch timestamp in ms from the 'Received' header (or 'internalDate' as a fall-back)
        """
        try:
            received_header = next(
                filter(lambda p: p["name"] == "Received", message["payload"]["headers"])
            )
            field = received_header["value"].split(";")[1]
            date = parser.parse(field)
            return date.timestamp() * 1000

        except:
            logger.exception(
                "couldn't parse the timestamp from the 'Received' header for message {} (fall-back to 'internalDate' field)".format(
                    message["id"]
                )
            )
            pprint(message)

            return int(message["internalDate"])
