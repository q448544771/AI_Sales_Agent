from sqlalchemy.orm import DeclarativeBase


from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Text
from sqlalchemy import DateTime



class Base(DeclarativeBase):
    pass




class Lead(Base):


    # 对应数据库表名
    __tablename__ = "leads"



    id = Column(
        Integer,
        primary_key=True
    )



    company = Column(
        String(100)
    )



    industry = Column(
        String(100)
    )



    region = Column(
        String(50)
    )



    score = Column(
        Float
    )



    level = Column(
        String(20)
    )



    evidence = Column(
        Text
    )



    action = Column(
        Text
    )



    # =====================
    # CRM生命周期字段
    # =====================


    # 当前销售阶段
    #
    # new
    # contacted
    # qualified
    # meeting
    # proposal
    # negotiation
    # won
    # lost

    stage = Column(
        String(50),
        default="new"
    )



    # 最近一次联系时间

    last_contact_time = Column(
        DateTime,
        nullable=True
    )



    # 下一步销售动作

    next_action = Column(
        Text,
        nullable=True
    )



    # 销售负责人

    owner = Column(
        String(50),
        nullable=True
    )



    # 数据状态
    #
    # new
    # updated

    status = Column(
        String(50),
        default="new"
    )