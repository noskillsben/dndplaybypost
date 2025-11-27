from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from services.dice_roller import DiceRoller, DiceRollResult

router = APIRouter(prefix="/dice", tags=["dice"])

dice_roller = DiceRoller()


class RollRequest(BaseModel):
    expression: str


class MultiRollRequest(BaseModel):
    expressions: List[str]


@router.post("/roll", response_model=DiceRollResult)
async def roll_dice(request: RollRequest):
    """
    Roll dice using standard notation.
    
    Examples:
    - "1d20" - Roll one 20-sided die
    - "1d20+5" - Roll one 20-sided die and add 5
    - "2d6" - Roll two 6-sided dice
    - "1d20-2" - Roll one 20-sided die and subtract 2
    """
    try:
        result = dice_roller.roll(request.expression)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/roll/multiple", response_model=List[DiceRollResult])
async def roll_multiple_dice(request: MultiRollRequest):
    """
    Roll multiple dice expressions at once.
    
    Example:
    {
      "expressions": ["1d20+5", "2d6", "1d8+3"]
    }
    """
    try:
        results = dice_roller.roll_multiple(request.expressions)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
