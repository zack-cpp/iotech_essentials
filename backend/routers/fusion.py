from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import simpleeval
import math

from database import get_db, SensorFusionRule
from config import get_settings
from schemas import (
    SensorFusionRuleCreate,
    SensorFusionRuleUpdate,
    SensorFusionRuleResponse,
    SensorFusionValidateRequest
)

router = APIRouter(prefix="/api/fusion-rules", tags=["Sensor Fusion"])
settings = get_settings()


# Common simpleeval setup for safe evaluation
def create_evaluator():
    s = simpleeval.SimpleEval()
    s.functions.update(math.__dict__)
    return s


@router.get("", response_model=list[SensorFusionRuleResponse])
def list_rules(db: Session = Depends(get_db)):
    """List all Sensor Fusion rules for this gateway."""
    return db.query(SensorFusionRule).filter(
        SensorFusionRule.gateway_id == settings.GATEWAY_ID
    ).all()


@router.get("/{rule_id}", response_model=SensorFusionRuleResponse)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(SensorFusionRule).filter(SensorFusionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("", response_model=SensorFusionRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(rule_in: SensorFusionRuleCreate, db: Session = Depends(get_db)):
    # Validate the formula first
    evaluator = create_evaluator()
    # E.g., if source_field is 'voltage', we expect '<voltage>' or similar.
    # The requirement is placeholder for source values (e.g. <source_1>)
    # So we'll assign a dummy value to 'source_1'
    evaluator.names = {"source_1": 1.0}
    try:
        formula_to_eval = rule_in.formula.replace("<source_1>", "source_1")
        evaluator.eval(formula_to_eval)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Formula validation failed: {str(e)}")

    rule_data = rule_in.model_dump()
    rule_data["gateway_id"] = settings.GATEWAY_ID
    
    db_rule = SensorFusionRule(**rule_data)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.put("/{rule_id}", response_model=SensorFusionRuleResponse)
def update_rule(rule_id: int, rule_in: SensorFusionRuleUpdate, db: Session = Depends(get_db)):
    db_rule = db.query(SensorFusionRule).filter(SensorFusionRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Validate formula
    evaluator = create_evaluator()
    evaluator.names = {"source_1": 1.0}
    try:
        formula_to_eval = rule_in.formula.replace("<source_1>", "source_1")
        evaluator.eval(formula_to_eval)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Formula validation failed: {str(e)}")

    update_data = rule_in.model_dump(exclude_unset=True)
    update_data.pop("gateway_id", None)  # Ensure gateway ID isn't overridden
    
    for k, v in update_data.items():
        setattr(db_rule, k, v)

    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(SensorFusionRule).filter(SensorFusionRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    db.delete(db_rule)
    db.commit()
    return {"message": "Rule deleted", "id": rule_id}


@router.post("/validate")
def validate_formula(req: SensorFusionValidateRequest):
    """Dry-run endpoint to validate a formula with a dummy value."""
    evaluator = create_evaluator()
    evaluator.names = {"source_1": req.dummy_value}
    
    try:
        formula_to_eval = req.formula.replace("<source_1>", "source_1")
        result = evaluator.eval(formula_to_eval)
        return {"valid": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid formula: {str(e)}")
