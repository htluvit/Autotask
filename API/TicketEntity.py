import mysql.connector, time
from datetime import datetime, timedelta
from freedom_config import *

class smallTicket():
    def __init__(self, accountID, dueDate, id, priority, status, title):
        self.autotaskConnector = AutotaskConnector()
        self.autotaskCient = self.autotaskConnector.login()
        self.ticket = self.autotaskCient.factory.create('Ticket')
        self.accountID = accountID
        self.dueDate = dueDate
        self.id = id
        self.priority = priority
        self.status = status
        self.title = title

        self.ticket.accountID = self.accountID
        self.ticket.dueDate = self.dueDate
        self.ticket.id = self.id
        self.ticket.priority = self.priority
        self.ticket.status = self.status
        self.ticket.title = self.title

    def _getTicket(self):
        return self.ticket

class SMSTicket(smallTicket):
    def __init__(self, smallTicket):
        self.ticket = smallTicket._getTicket()
        self.
