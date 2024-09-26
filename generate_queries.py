from openai import OpenAI
import instructor
import instructor.patch
from instructor import Mode
from pydantic import BaseModel
import os
import json
import asyncio
import random


async def static_generation():
    with open("./data/opentable_restaurants.json", "r") as file:
        data = json.load(file)

        queries = []
        people = [2,3,4,5,6,7,8,9,10]
        time = ["6:00 PM", "6:30 PM", "7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM", "9:00 PM", "9:30 PM", "10:00 PM", "10:30 PM"]
        dates = ["2024-09-27", "2024-09-28", "2024-09-29", "2024-09-30", "2024-10-01", "2024-10-02", "2024-10-03", "2024-10-04", "2024-10-05", "2024-10-06", "2024-10-07", "2024-10-08", "2024-10-09", "2024-10-10", "2024-10-11"]
        dummy_phone = ["9876543210", "9876543211", "9876543212", "9876543213", "9876543214", "9876543215", "9876543216", "9876543217", "9876543218", "9876543219"]

        for restaurant in data:
            num_people = random.choice(people)
            booking_time = random.choice(time)
            booking_date = random.choice(dates)
            phone_number = random.choice(dummy_phone)

            query = f"Book a table for {num_people} people at {restaurant['name']} in {restaurant['city']} on {booking_date} at {booking_time}. Use the following phone number: {phone_number}."
            queries.append(query)
            print(query)
        
        with open("./data/dataset.json", "w", encoding="utf-8") as jsonfile:
            json.dump(queries, jsonfile, ensure_ascii=False, indent=2)

async def ai_generation():
    oai = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    )

    client = instructor.from_openai(oai, mode=Mode.JSON)

    class Output(BaseModel):
        time: str
        date: str
        number_of_people: int
        dummy_phone: str

    class Input(BaseModel):
        restaurant_name: str
        city: str

    messages = [
        {"role": "system", "content": """
        You are given the name and city of a restaurant. You will output the following information - 
        1. A time - between 6PM and 10PM to book the restaurant.
        2. A date today is 26th September 2024 - so any day after it in the next one week works fine. 
        3. Number of people going to the restaurant - keep this between 2 and 10.
        4. A dummy indian phone number without the +91 prefix that will be used to create the booking 
        This will be used to curate a dataset of user goals around restaturant bookings on opentable.
        """},
        ]

    with open("./data/opentable_restaurants.json", "r") as file:
        data = json.load(file)

        queries = []

        for i in data:
            input: Input = Input(restaurant_name=i["name"], city=i["city"])
            messages.append({"role": "user", "content": f"Restaurant name: {input.restaurant_name}, City: {input.city}"})
            completion:Output = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                response_model=Output,
                temperature=0.8,
            )
            if i==0: 
                print(completion)
            
            queries.append(f"Book a table for {completion.number_of_people} people at {input.restaurant_name} in {input.city} on {completion.date} at {completion.time}. Use the following phone number: {completion.dummy_phone}.")
            print(queries[-1])
        
        with open("./data/dataset.json", "w", encoding="utf-8") as jsonfile:
            json.dump(queries, jsonfile, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    asyncio.run(static_generation())
