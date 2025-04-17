from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uvicorn
import json
import os

app = FastAPI()

# Pydantic model for ticket
class Ticket(BaseModel):
    id: int
    title: str
    description: str
    status: str = "open"
    created_at: datetime

# JSON file for storage, using /data directory for Fly Volume
TICKETS_FILE = "/data/tickets.json"

# Load tickets from JSON file
def load_tickets():
    if not os.path.exists(TICKETS_FILE):
        return {"tickets": [], "ticket_id_counter": 1}
    with open(TICKETS_FILE, "r") as f:
        data = json.load(f)
        # Convert created_at strings back to datetime
        for ticket in data["tickets"]:
            ticket["created_at"] = datetime.fromisoformat(ticket["created_at"])
        return data

# Save tickets to JSON file
def save_tickets(tickets, ticket_id_counter):
    # Ensure the /data directory exists
    os.makedirs(os.path.dirname(TICKETS_FILE), exist_ok=True)
    with open(TICKETS_FILE, "w") as f:
        # Convert tickets to dict and created_at to string for JSON serialization
        serializable_tickets = [
            {**ticket.dict(), "created_at": ticket.created_at.isoformat()}
            for ticket in tickets
        ]
        json.dump({"tickets": serializable_tickets, "ticket_id_counter": ticket_id_counter}, f, indent=2)

# Initialize tickets and counter
data = load_tickets()
tickets = [Ticket(**ticket) for ticket in data["tickets"]]
ticket_id_counter = data["ticket_id_counter"]

# Create a ticket
@app.post("/tickets", response_model=Ticket)
async def create_ticket(title: str, description: str):
    global ticket_id_counter
    ticket = Ticket(
        id=ticket_id_counter,
        title=title,
        description=description,
        status="open",
        created_at=datetime.utcnow()
    )
    tickets.append(ticket)
    ticket_id_counter += 1
    save_tickets(tickets, ticket_id_counter)
    return ticket

# Get ticket status
@app.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: int):
    for ticket in tickets:
        if ticket.id == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail="Ticket not found")

# Delete a ticket
@app.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: int):
    for i, ticket in enumerate(tickets):
        if ticket.id == ticket_id:
            tickets.pop(i)
            save_tickets(tickets, ticket_id_counter)
            return {"message": "Ticket deleted"}
    raise HTTPException(status_code=404, detail="Ticket not found")

# List all tickets
@app.get("/tickets", response_model=List[Ticket])
async def list_tickets():
    return tickets

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)