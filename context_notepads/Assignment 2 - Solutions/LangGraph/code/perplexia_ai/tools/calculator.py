import re
from typing import Union

class Calculator:
    """A simple calculator tool for evaluating basic arithmetic expressions."""
    
    @staticmethod
    def evaluate_expression(expression: str) -> Union[float, str]:
        """Evaluate a basic arithmetic expression.
        
        Supports only basic arithmetic operations (+, -, *, /) and parentheses.
        Returns an error message if the expression is invalid or cannot be 
        evaluated safely.
        
        Args:
            expression: A string containing a mathematical expression
                       e.g. "5 + 3" or "10 * (2 + 3)"
            
        Returns:
            Union[float, str]: The result of the evaluation, or an error message
                              if the expression is invalid
        
        Examples:
            >>> Calculator.evaluate_expression("5 + 3")
            8.0
            >>> Calculator.evaluate_expression("10 * (2 + 3)")
            50.0
            >>> Calculator.evaluate_expression("15 / 3")
            5.0
        """
        try:
            # Clean up the expression
            expression = expression.strip()
            
            # Only allow safe characters (digits, basic operators, parentheses, spaces)
            if not re.match(r'^[\d\s\+\-\*\/\(\)\.]*$', expression):
                return "Error: Invalid characters in expression"
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}})
            
            # Convert to float and handle division by zero
            return float(result)
            
        except ZeroDivisionError:
            return "Error: Division by zero"
        except (SyntaxError, TypeError, NameError):
            return "Error: Invalid expression"
        except Exception as e:
            return f"Error: {str(e)}"
