from dataclasses import dataclass

from dataclass_wizard import JSONWizard, json_field


@dataclass
class Gift(JSONWizard):
    id: int
    type: str
    price: int

    def compact(self):
        return f"Gift(id:{self.id:4}, {self.type:15}, price:{self.price})"


@dataclass
class Child(JSONWizard):
    id: int
    gender: str
    age: int

    def compact(self):
        return f"Child(id:{self.id:4}, {self.gender:6}, age:{self.age:2})"


@dataclass
class Map(JSONWizard):
    gifts: list[Gift]
    children: list[Child]


# Order classes

@dataclass
class Present(JSONWizard):
    gift_id: int = json_field("giftID", all=True)
    child_id: int = json_field("childID", all=True)


@dataclass
class Order(JSONWizard):
    map_id: str = json_field("mapID", all=True)
    presenting_gifts: list[Present] = json_field("presentingGifts", all=True)


@dataclass
class OrderResponse(JSONWizard):
    success: bool
    error: str
    round_id: str


# Status classes

@dataclass
class RoundInfoData(JSONWizard):
    error_message: str = json_field("error_message")
    status: str = json_field("status")
    total_happy: int = json_field("total_happy")


@dataclass
class RoundInfo(JSONWizard):
    success: bool
    error: str
    data: RoundInfoData
