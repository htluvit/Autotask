import mysql.connector, time
from datetime import datetime, timedelta
from freedom_config import *


class TicketSMS():
    def __init__(self):
        self.autotaskConnector = AutotaskConnector()
        self.autotaskCient = self.autotaskConnector.login()

        self.mysqlConnector = MySQLConnector()
        self.mysqlClient = self.mysqlConnector.login()
        self.myCursor = self.mysqlClient.cursor()

class TicketSMS():
    def __init__(self):
        self.autotaskConnector = AutotaskConnector()
        self.autotaskCient = self.autotaskConnector.login()

        self.mysqlConnector = MySQLConnector()
        self.mysqlClient = self.mysqlConnector.login()
        self.myCursor = self.mysqlClient.cursor()

    def _get_Text(self):
        query = ("select * from messagein where TicketNoteID is NULL;")
        self.myCursor.execute(query)
        texts = []
        for id in reversed(list(self.myCursor)):
            texts.append(id)
        if len(texts) > 0:
            print("New Text From "+texts[-1][3]+"! Processing..")
            return texts[-1]


    def _searchTicket(self,text):

        String = '<queryxml><entity>Ticket</entity><query>' \
                 '<field>Title<expression op="Contains">' + str(text[3]) + '</expression></field>' \
                 '<field>Source<expression op="equals">15</expression></field>' \
                 '<field>Status<expression op="NotEqual">5</expression></field>' \
                 '</query></queryxml>'

        searchTicketQuery = self.autotaskCient.service.query(String)
        while not searchTicketQuery['ReturnCode'] == 1:
            self._reconnect_autotask()
            time.sleep(3)
            searchTicketQuery = self.autotaskCient.service.query(String)
        if not searchTicketQuery['EntityResults'] == '':
            ticketNumber = searchTicketQuery['EntityResults']['Entity'][0]['TicketNumber']
            print("Existing Ticket Found! Ticket Number : "+str(ticketNumber))
            return searchTicketQuery['EntityResults']['Entity'][0]
        else:
            print("No Existing Ticket Found!")

    def _createTicket(self, text):
        createTicketArray = self.autotaskCient.factory.create('ArrayOfEntity')
        createTicket = self.autotaskCient.factory.create('Ticket')
        createTicket.id = 0
        createTicket.AccountID = 295
        createTicket.Source = 15
        createTicket.Status = 1
        createTicket.Priority = 2
        createTicket.QueueID = 29683485

        createTicket.DueDateTime = datetime.now()
        createTicket.ServiceLevelAgreementID = 9
        createTicket.Title = str(text[3])+": "+ str(text[6][:50])
        udf = self.autotaskCient.factory.create('UserDefinedField')
        udf.Name = 'Phone'
        udf.Value = text[3]
        createTicket.UserDefinedFields.UserDefinedField.append(udf)
        createTicketArray.Entity.append(createTicket)
        createTicketQuery = self.autotaskCient.service.create(createTicketArray)
        while not createTicketQuery['ReturnCode'] == 1:
            print(createTicketArray)
            print(createTicketQuery)
            self._reconnect_autotask()
            time.sleep(3)
            createTicketQuery = self.autotaskCient.service.create(createTicketArray)
        ticketNumber = createTicketQuery['EntityResults']['Entity'][0]['TicketNumber']
        ticketID = createTicketQuery['EntityResults']['Entity'][0]['id']
        print("New Ticket Created! Ticket Number : "+str(ticketNumber))
        return ticketID

    def _updateTicket(self, text, existingTicket):
        updateTicketArray = self.autotaskCient.factory.create('ArrayOfEntity')
        updateTicket = self.autotaskCient.factory.create('Ticket')
        updateTicket.id = existingTicket['id']
        if 'AccountID' in existingTicket and existingTicket['AccountID']:
            updateTicket.AccountID = existingTicket['AccountID']
        if 'Description' in existingTicket and existingTicket['Description']:
            updateTicket.Description = existingTicket['Description']
        if 'AllocationCodeID' in existingTicket and existingTicket['AllocationCodeID']:
            updateTicket.AllocationCodeID = existingTicket['AllocationCodeID']
        if 'AssignedResourceID' in existingTicket and existingTicket['AssignedResourceID']:
            updateTicket.AssignedResourceID = existingTicket['AssignedResourceID']
        if 'AssignedResourceRoleID' in existingTicket and existingTicket['AssignedResourceRoleID']:
            updateTicket.AssignedResourceRoleID = existingTicket['AssignedResourceRoleID']
        if 'Priority' in existingTicket and existingTicket['Priority']:
            updateTicket.Priority = existingTicket['Priority']
        if 'Title' in existingTicket and existingTicket['Title']:
            updateTicket.Title = existingTicket['Title']
        if 'TicketType' in existingTicket and existingTicket['TicketType']:
            updateTicket.TicketType = existingTicket['TicketType']
        if 'QueueID' in existingTicket and existingTicket['QueueID']:
            updateTicket.QueueID = existingTicket['QueueID']
        updateTicket.DueDateTime = datetime.now() + timedelta(hours=1)
        updateTicket.Source = 15
        updateTicket.Status = 20
        
        updateTicket.ServiceLevelAgreementID = 9

        updateTicketArray.Entity.append(updateTicket)
        updateTicketQuery = self.autotaskCient.service.update(updateTicketArray)
        while not updateTicketQuery['ReturnCode'] == 1:
            print(updateTicketArray)
            print(updateTicketQuery)
            self._reconnect_autotask()
            time.sleep(3)
            updateTicketQuery = self.autotaskCient.service.update(updateTicketArray)
        ticketNumber = updateTicketQuery['EntityResults']['Entity'][0]['TicketNumber']
        ticketID = updateTicketQuery['EntityResults']['Entity'][0]['id']
        print("Existing Ticket Updated! Ticket Number : "+str(ticketNumber))
        return ticketID

    def _createTicketNote(self, text, ticketID):
        TickNoteArray = self.autotaskCient.factory.create('ArrayOfEntity')
        ticketNote = self.autotaskCient.factory.create('TicketNote')
        ticketNote.id = 0

        ticketNote.Title = "Customer replied at: " + str(text[1])
        ticketNote.Description = str(text[6][:3000])
        ticketNote.TicketID = ticketID
        ticketNote.Publish = 2
        ticketNote.NoteType = 1
        TickNoteArray.Entity.append(ticketNote)
        createTicketNoteQuery = self.autotaskCient.service.create(TickNoteArray)
        while not createTicketNoteQuery['ReturnCode'] == 1:
            print(TickNoteArray)
            print(createTicketNoteQuery)
            self._reconnect_autotask()
            time.sleep(3)
            createTicketNoteQuery = self.autotaskCient.service.create(TickNoteArray)
        ticketNoteID = createTicketNoteQuery['EntityResults']['Entity'][0]['id']
        print("New Ticket Note Created! Ticket Number : "+str(ticketNoteID))
        return ticketNoteID

    def _updateDatabase(self, text, TicketID, TicketNoteID):
        update_row = ("UPDATE messagein SET TicketID = %s, TicketNoteID = %s WHERE ID = %s;")
        self.myCursor.execute(update_row, (TicketID, TicketNoteID, text[0]))
        self.mysqlClient.commit()
        verify = ("select * from messagein where TicketID = %s and TicketNoteID = %s and ID = %s;")
        self.myCursor.execute(verify, (TicketID, TicketNoteID, text[0]))
        a = list(self.myCursor)
        if a[0][11] == str(TicketID) and a[0][12] == str(TicketNoteID):
            print("Entry Verified!")
        else:
            print("Failed To Update Database!")

    def _reconnect_autotask(self):
        self.autotaskConnector = AutotaskConnector()
        self.autotaskCient = self.autotaskConnector.login()

    def _reconnect_mysql(self):
        self.mysqlConnector = MySQLConnector()
        self.mysqlClient = self.mysqlConnector.login()
        self.myCursor = self.mysqlClient.cursor()

    def _process(self):
        text = self._get_Text()
        if not text is None:
            existingTicket = self._searchTicket(text)
            if existingTicket is None:
                print("Creating ticket...")
                newTicketID = self._createTicket(text)
                print("Creating ticket note...")
                newTicketNoteID = self._createTicketNote(text, newTicketID)
                print("Updating Database...")
                self._updateDatabase(text, newTicketID, newTicketNoteID)
                print("Text From "+text[3]+" Processed!")
            else:
                existingTicketID = existingTicket['id']
                print("Creating Ticket Note...")
                newTicketNoteID = self._createTicketNote(text, existingTicketID)
                print("Updating Ticket...")
                updatedTicketID = self._updateTicket(text,existingTicket)
                print("Updating Database...")
                self._updateDatabase(text, updatedTicketID, newTicketNoteID)
                print("Text From "+text[3]+" Processed!")
        
        self.mysqlClient.commit()
        time.sleep(10)

main = TicketSMS()
while 1:
    main._process()


