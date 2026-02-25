from typing import Tuple

from petta import PeTTa                                                                                                                                                                

def balance_parentheses(expr: str) -> Tuple[str,float]:
    score = 1.0
    """Balance parentheses in an expression by adding or removing at the end."""
    # Add opening parenthesis if expression starts with colon
    if expr.startswith(':'):
        expr = '(' + expr
        score = 0.6
        
    open_count = expr.count('(')
    close_count = expr.count(')')
    
    if open_count > close_count:
        # Add missing closing parentheses
        return expr + ')' * (open_count - close_count) , score - 0.4
    elif close_count > open_count:
        # Remove only excess closing parentheses from the end
        excess = close_count - open_count
        i = len(expr) - 1
        
        # First verify the end of string contains only closing parentheses
        while i >= 0 and excess > 0:
            if expr[i] != ')':
                # Found non-parenthesis - give up and return original
                return expr , 0
            i -= 1
            excess -= 1
            
        # If we got here, we found enough closing parentheses at the end
        # Now remove the exact number of excess ones
        excess = close_count - open_count
        return expr[:-excess] , score - 0.4
    return expr , score

def _run_petta_check(expr: str, pattern: str,
                     value_if_var: float,
                     value_if_nonvar: float) -> float:
    petta = PeTTa()
    code = (
        f"!(if (= {expr} {pattern}) "
        f"(if (== (get-metatype $123prf) Variable) {value_if_var} {value_if_nonvar}) "
        f"0.0)"
    )

    try:
        res = petta.process_metta_string(code)[0]
        return float(res)
    except Exception:
        return 0.0

def checkStmt(expr: str) -> float:
    pattern = "(: $123prf $123stmt (STV $123s $123c))"
    return _run_petta_check(expr, pattern, value_if_var=0.0, value_if_nonvar=1.0)

def checkImpl(expr: str) -> float:
    pattern = "(: $123prf (Implication (cons Premises $123654a) (cons Conclusions $123654b)) (STV $123s $123c))"
    return _run_petta_check(expr, pattern, value_if_var=0.0, value_if_nonvar=1.0)

def checkQuery(expr: str) -> float:
    pattern = "(: $123prf $123stmt $123tv)"
    return _run_petta_check(expr, pattern, value_if_var=1.0, value_if_nonvar=0.0)

if __name__ == "__main__":
    print(checkStmt("(: prf foo (STV 1.0 1.0)"))
