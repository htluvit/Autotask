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

    def _get_Incoming_Text(self):
        query = ("select * from messagein where TicketNoteID is NULL;")
        self.myCursor.execute(query)
        texts = []
        for id in reversed(list(self.myCursor)):
            texts.append(id)
        if len(texts) > 0:
            
            print("New Text From " + texts[-1][3] + "! Processing..")
            return texts[-1]

    def _get_Outgoing_Text(self):
        query = ("select id, SendTime, StatusCode, MessageTo, MessageFrom, TicketID, MessageText from messagelog where TicketID is NULL;")
        self.myCursor.execute(query)
        texts = []
        for id in reversed(list(self.myCursor)):
            texts.append(id)
        if len(texts) > 0:
            
            print("Text Sent To " + texts[-1][3] + " From Support! Processing..")
            return texts[-1]

    def _searchTicket(self, text):
        String = '<queryxml><entity>Ticket</entity><query>' \
                 '<field udf="true">Phone<expression op="Contains">' + str(text[3]) + '</expression></field>' \
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
            print("Existing Ticket Found! Ticket Number : " + str(ticketNumber))
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
        createTicket.ServiceLevelAgreementID = 1
        createTicket.Title = str(text[3]) + ": " + str(text[6][:50])
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
        createdTicket = createTicketQuery['EntityResults']['Entity'][0]
        ticketNumber = createdTicket['TicketNumber']
        ticketID = createdTicket['id']
        print("New Ticket Created! Ticket Number : " + str(ticketNumber))
        return createdTicket

    def _updateTicket(self, text, existingTicket, status):
        TN = '<queryxml><entity>TicketNote</entity><query>' \
                     '<field>TicketID<expression op="Equals">' + str(existingTicket['id']) + '</expression></field>' \
                     '</query></queryxml>'
        workflowFired = False
        while not workflowFired:
            time.sleep(2)
            query = self.autotaskCient.service.query(TN)
            lastTN = query['EntityResults']['Entity'][-1]
            workflowFired = lastTN['CreatorResourceID'] == 4
            print("Waiting For Workflow Rule...")

        updateTicketArray = self.autotaskCient.factory.create('ArrayOfEntity')
        updateTicket = self.autotaskCient.factory.create('Ticket')
        updateTicket.id = existingTicket['id']
        if 'AccountID' in existingTicket and existingTicket['AccountID']:
            updateTicket.AccountID = existingTicket['AccountID']
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
        if 'IssueType' in existingTicket and existingTicket['IssueType']:
            updateTicket.IssueType = existingTicket['IssueType']
        if 'SubIssueType' in existingTicket and existingTicket['SubIssueType']:
            updateTicket.SubIssueType = existingTicket['SubIssueType']
        if 'QueueID' in existingTicket and existingTicket['QueueID']:
            updateTicket.QueueID = existingTicket['QueueID']

        updateTicket.Description = self._get_conv(text)
        updateTicket.DueDateTime = datetime.now() + timedelta(hours=1)
        updateTicket.Source = 15
        updateTicket.Status = int(status)

        updateTicket.ServiceLevelAgreementID = 1

        updateTicketArray.Entity.append(updateTicket)
        updateTicketQuery = self.autotaskCient.service.update(updateTicketArray)
        while not updateTicketQuery['ReturnCode'] == 1:
            print(updateTicketArray)
            print(updateTicketQuery)
            self._reconnect_autotask()
            time.sleep(3)
            updateTicketQuery = self.autotaskCient.service.update(updateTicketArray)
        updatedTicket = updateTicketQuery['EntityResults']['Entity'][0]
        ticketNumber = updatedTicket['TicketNumber']
        print("Existing Ticket Updated! Ticket Number : " + str(ticketNumber))

        return updatedTicket

    def _createTicketNote(self, text, createdTicket, case):
        TickNoteArray = self.autotaskCient.factory.create('ArrayOfEntity')
        ticketNote = self.autotaskCient.factory.create('TicketNote')
        ticketNote.id = 0

        if case == 20:
            ticketNote.Title = "Customer replied at: " + str(text[1])
            ticketNote.Description = str(text[6][:3000])
        elif case == 0:
            ticketNote.Title = "Attention! Message Sent at: " + str(text[1])
            ticketNote.Description = "Message was NOT sent to "+str(text[3])+"!"

        ticketNote.TicketID = createdTicket['id']
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
        createdTicketNote = createTicketNoteQuery['EntityResults']['Entity'][0]
        ticketNoteID = createdTicketNote['id']
        print("New Ticket Note Created! Ticket Note Number : " + str(ticketNoteID))
        return createdTicketNote

    def _updateDatabase(self, text, ticket, createdTicketNote):
        update_row = ("UPDATE messagein SET TicketID = %s, TicketNoteID = %s WHERE ID = %s;")
        TicketNoteID = createdTicketNote['id']
        TicketID = ticket['id']
        self.myCursor.execute(update_row, (TicketID, TicketNoteID, text[0]))
        self.mysqlClient.commit()
        verify = ("select * from messagein where TicketID = %s and TicketNoteID = %s and ID = %s;")
        self.myCursor.execute(verify, (TicketID, TicketNoteID, text[0]))
        a = list(self.myCursor)
        if a[0][11] == str(TicketID) and a[0][12] == str(TicketNoteID):
            print("Entry Verified!")
        else:
            print("Failed To Update Database!")

    def _get_conv(self, text):

        phoneNumber = str(text[3])
        texts = []

        self.myCursor.execute('select id, SendTime, MessageFrom, MessageText, SMSC from messagein where MessageFrom = '+phoneNumber+';')
        for id in list(self.myCursor):
            texts.append(id)

        self.mysqlClient.commit()

        self.myCursor.execute('select id, SendTime, MessageFrom, MessageText , StatusCode from messagelog where MessageTo = '+phoneNumber+';')
        for id in list(self.myCursor):
            texts.append(id)

        texts.sort(key=lambda x: x[1])
        conv = ''
        for t in list(texts[-15:]):
            time = str(t[1])
            msg = str(t[3])
            rep = ''
            status = ''

            if None == t[2]:
                rep = ' Support    '
            else:
                rep = str(t[2])

            if 200 == t[4] or t[4]== None:
                status = ' (Success) '
            else:
                status = ' (Fail, Please Retry)'

            conv += time + " " + rep + ": " + status + msg + '\n'+ '\n'
        self.mysqlClient.commit()
        return conv

    def _reconnect_autotask(self):
        self.autotaskConnector = AutotaskConnector()
        self.autotaskCient = self.autotaskConnector.login()

    def _reconnect_mysql(self):
        self.mysqlConnector = MySQLConnector()
        self.mysqlClient = self.mysqlConnector.login()
        self.myCursor = self.mysqlClient.cursor()

    def _process(self):
        incomingText = self._get_Incoming_Text()
        if not incomingText is None:
            existingTicket = self._searchTicket(incomingText)
            if existingTicket is None:
                print("Creating ticket...")
                newTicket = self._createTicket(incomingText)
                print("Creating ticket note...")
                newTicketNote = self._createTicketNote(incomingText, newTicket, 20)
                print("Updating Ticket...")
                updatedTicket = self._updateTicket(incomingText, newTicket, 20)
                print("Updating Database...")
                self._updateDatabase(incomingText, updatedTicket, newTicketNote)
                print("Text From " + incomingText[3] + " Processed!")
                print("****************************************************")
            else:
                print("Creating Ticket Note...")
                newTicketNote = self._createTicketNote(incomingText, existingTicket, 20)
                print("Updating Ticket...")
                updatedTicket = self._updateTicket(incomingText, existingTicket, 20)
                print("Updating Database...")
                self._updateDatabase(incomingText, updatedTicket, newTicketNote)
                print("Text From " + incomingText[3] + " Processed!")
                print("****************************************************")
        self.mysqlClient.commit()

        outgoingText = self._get_Outgoing_Text()
        if not outgoingText is None:
            existingTicket1 = self._searchTicket(outgoingText)
            if existingTicket1 is None:
                if not outgoingText[2] == 200:
                    print("Creating ticket...")
                    newTicket1 = self._createTicket(outgoingText)
                    print("Message Not Sent! Creating Ticket Note...")
                    newTicketNote1 = self._createTicketNote(outgoingText, newTicket1, 0)
                    print("Updating Ticket...")
                    updatedTicket1 = self._updateTicket(outgoingText, newTicket1, 20)
                    print("Updating Database...")
                    update_row = ("UPDATE messagelog SET TicketID = "+str(updatedTicket1['id'])+" WHERE ID = "+str(+outgoingText[0])+";")
                    self.myCursor.execute(update_row)
                    self.mysqlClient.commit()
                    print("Outgoing Text To " + outgoingText[3] + " Processed!")
                    print("****************************************************")
                else:
                    print("Ticket Was Closed But The Text Was Sent Anyway...*Yawning*...I Am Too Lazy For This...Let's Just Backdoor Then..")
                    print("Updating Database...")
                    update_row = ("UPDATE messagelog SET TicketID = 'LazyFace' WHERE ID = "+str(+outgoingText[0])+";")
                    self.myCursor.execute(update_row)
                    self.mysqlClient.commit()
                    print("Outgoing Text To " + outgoingText[3] + " Processed!")
                    print("****************************************************")
            else:
                if not outgoingText[2] == 200:
                    print("Message Not Sent! Creating Ticket Note...")
                    newTicketNote1 = self._createTicketNote(outgoingText, existingTicket1, 0)
                    print("Updating Ticket...")
                    updatedTicket1 = self._updateTicket(outgoingText, existingTicket1, 20)
                    print("Updating Database...")
                    update_row = ("UPDATE messagelog SET TicketID = "+str(updatedTicket1['id'])+" WHERE ID = "+str(+outgoingText[0])+";")
                    self.myCursor.execute(update_row)
                    self.mysqlClient.commit()
                    print("Outgoing Text To " + outgoingText[3] + " Processed!")
                    print("****************************************************")
                else:
                    print("Updating Ticket...")
                    updatedTicket1 = self._updateTicket(outgoingText, existingTicket1, 7)
                    print("Updating Database...")
                    update_row = ("UPDATE messagelog SET TicketID = "+str(updatedTicket1['id'])+" WHERE ID = "+str(+outgoingText[0])+";")
                    self.myCursor.execute(update_row)
                    self.mysqlClient.commit()
                    print("Outgoing Text To " + outgoingText[3] + " Processed!")
                    print("****************************************************")
        self.mysqlClient.commit()
        time.sleep(10)


main = TicketSMS()
while 1:
    main._process()
    



