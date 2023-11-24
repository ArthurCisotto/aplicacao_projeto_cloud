from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

logging.basicConfig(level=logging.INFO, filename='app.log', 
                    format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

@app.post("/items/")
def create_item(name: str, description: str):
    try:
        db = SessionLocal()
        new_item = Item(name=name, description=description)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        logger.info(f"Item created with ID: {new_item.id}")
        return new_item
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items/{item_id}")
def read_item(item_id: int):
    try:
        db = SessionLocal()
        item = db.query(Item).filter(Item.id == item_id).first()
        if item is None:
            logger.warning(f"Item with ID {item_id} not found")
            raise HTTPException(status_code=404, detail="Item not found")
        logger.info(f"Item retrieved with ID: {item_id}")
        return item
    except Exception as e:
        logger.error(f"Error retrieving item: {e}")
        raise HTTPException(status_code=500, detail=str(e))
