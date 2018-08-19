from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User
import json

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = create_engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


user1 = User(name="Admin")
session.add(user1)
session.commit()


category_json = json.loads("""{
"all_categories": [
    {
        "id": 1,
        "name": "Soccer"
    },
    {
        "id": 2,
        "name": "Basketball"
    },
    {
        "id": 3,
        "name": "Baseball"
    },
    {
        "id": 4,
        "name": "Frisbee"
    },
    {
        "id": 5,
        "name": "Snowboarding"
    },
    {
        "id": 6,
        "name": "Rock Climbing"
    },
    {
        "id": 7,
        "name": "Foosball"
    },
    {
        "id": 8,
        "name": "Skating"
    },
    {
        "id": 9,
        "name": "Hockey"
    }
]
}""")

for e in category_json['all_categories']:
    category_input = Category(
        name=str(e['name']),
        id=int(e['id']),
        user_id=1
        )
    session.add(category_input)
    session.commit()


item_json = json.loads("""{
"all_items": [
    {
        "id": 1,
        "title": "Soccer Cleats",
        "description": "the classic soccer shoe with cleats/studs",
        "cat_id": 1
    },
    {
        "id": 2,
        "title": "Jersey",
        "description": "a strip or uniform",
        "cat_id": 1
    },
    {
        "id": 3,
        "title": "Shinguards",
        "description": "a stiff protective garment worn by hockey players",
        "cat_id": 1
    },
    {
        "id": 4,
        "title": "Two shinguards",
        "description": "a stiff protective garment worn by hockey players",
        "cat_id": 1
    },
    {
        "id": 5,
        "title": "Backboard",
        "description": "a raised vertical board with an attached basket",
        "cat_id": 2
    },
    {
        "id": 6,
        "title": "Bat",
        "description": "a smooth wooden or metal club used in baseball",
        "cat_id": 3
    },
    {
        "id": 7,
        "title": "Frisbee",
        "description": "a gliding toy or sporting item",
        "cat_id": 4
    },
    {
        "id": 8,
        "title": "Snowboard",
        "description": "Best for any terrain and conditions",
        "cat_id": 5
    },
    {
        "id": 9,
        "title": "Goggles",
        "description": "protective eyewear that protect the eye",
        "cat_id": 5
    },
    {
        "id": 10,
        "title": "Stick",
        "description": "a long, thin implement with a curved end to hit ball",
        "cat_id": 9
    }
]
}""")

for e in item_json['all_items']:
    item_input = Item(
        title=(e['title']),
        id=int(e['id']),
        description=str(e['description']),
        cat_id=int(e['cat_id']),
        user_id=1
        )
    session.add(category_input)
    session.commit()


print "added catalog items!"
