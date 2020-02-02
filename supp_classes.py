class Group:
    def __init__(self, name, owner_id):
        self.name = name
        self.owner_id = owner_id
        self.members = {}

    def add_member(self, member_id):
        self.members[member_id]


class Member:
    def __init__(self, id, fullname):
        self.id = id
        self.fullname = fullname
        self.reports = {}

    def add_report(self, datetime, report):
        date = datetime.date
        time = datetime.time
        self.reports[date] = report
        return