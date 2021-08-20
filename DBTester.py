from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from DBStructure import *

engine = create_engine(DBPATH)

# DBSession = sessionmaker(bind=engine)

test_user = User(username="test1", password=ascii_to_base64("123456"), email="cumfast.gmail.com")
test_resource = Resource(title="How to do edging", resource_link="127.0.0.1:8080",
                         difficulty=ResourceDifficulty.EASY)

# foreign key
test_resource_creater = ResourceCreater(rid=1, uid=1)


# insertion test
with Session(engine) as conn:
    conn.add(test_user)
    conn.add(test_resource)
    conn.add(test_resource_creater)
    conn.commit()

# view table test
with Session(engine) as conn:
    for i in conn.query(User).all():
        print(i)

    for i in conn.query(Resource).all():
        print(i)

    for i in conn.query(ResourceCreater).all():
        print(i)
