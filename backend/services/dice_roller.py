import re
import random
from typing import Dict, List, Optional
from pydantic import BaseModel


class DiceRollResult(BaseModel):
    """Result of a dice roll"""
    expression: str
    total: int
    rolls: List[int]
    breakdown: str


class DiceRoller:
    """Simple dice roller supporting standard notation"""
    
    def __init__(self):
        # Pattern: XdY+Z or XdY-Z or XdY
        self.pattern = re.compile(r'(\d+)d(\d+)([+-]\d+)?')
    
    def roll(self, expression: str) -> DiceRollResult:
        """
        Roll dice from an expression like "1d20+5" or "2d6"
        
        Args:
            expression: Dice expression (e.g., "1d20+5", "2d6", "1d20-2")
            
        Returns:
            DiceRollResult with total, individual rolls, and breakdown
        """
        expression = expression.strip().lower().replace(" ", "")
        
        match = self.pattern.match(expression)
        if not match:
            raise ValueError(f"Invalid dice expression: {expression}")
        
        num_dice = int(match.group(1))
        die_size = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        # Validate
        if num_dice < 1 or num_dice > 100:
            raise ValueError("Number of dice must be between 1 and 100")
        if die_size < 2 or die_size > 1000:
            raise ValueError("Die size must be between 2 and 1000")
        
        # Roll the dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        dice_total = sum(rolls)
        total = dice_total + modifier
        
        # Create breakdown string
        if num_dice == 1:
            breakdown = f"[{rolls[0]}]"
        else:
            breakdown = f"[{', '.join(map(str, rolls))}] = {dice_total}"
        
        if modifier != 0:
            breakdown += f" {modifier:+d} = {total}"
        
        return DiceRollResult(
            expression=expression,
            total=total,
            rolls=rolls,
            breakdown=breakdown
        )
    
    def roll_multiple(self, expressions: List[str]) -> List[DiceRollResult]:
        """Roll multiple dice expressions"""
        return [self.roll(expr) for expr in expressions]
