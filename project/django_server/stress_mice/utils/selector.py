import io
import sys

class Formula:
    def get_leaves(self):
        pass

class Clause(Formula):
    def __init__(self, clause):
        self.clause = clause
        
    def totree(self, padding = ""):
        return padding + self.clause
    
    def __str__(self):
        return self.clause
    
    def __len__(self):
        return 1
    
    def get_leaves(self):
        return [self.clause]

# class NotFormula(Clause):
#     def __init__(self, formula):
#         Clause.__init__(self, formula)
#         
#     def __str__(self):
#         return "!" + str(self.clause)
#     
#     def get_leaves(self):
#         return [self.clause]

class BinaryFormula(Formula):
    def __init__(self, left_formula, operator, right_formula):
        self.operator = operator
        self.left_formula = left_formula
        self.right_formula = right_formula
    
    def totree(self, padding = ""):
        final = ""
        final += self.left_formula.totree(padding + "\t") + "\n"
        final += padding + str(self.operator) + "\n"
        final += self.right_formula.totree(padding + "\t")
        return final
    
    def __str__(self):
        return "(" + str(self.left_formula) + ") " + str(self.operator) + " (" + str(self.right_formula) + " )"
    
    def __len__(self):
        left_contribute = 2 if isinstance(self.left_formula, BinaryFormula) else 0
        right_contribute = 2 if isinstance(self.right_formula, BinaryFormula) else 0
        return len(self.left_formula) + len(self.right_formula) + 1 + left_contribute + right_contribute
    
    def get_leaves(self):
        return self.left_formula.get_leaves() + self.right_formula.get_leaves()

class OrFormula(BinaryFormula):
    def __init__(self, left_formula, right_formula):
        BinaryFormula.__init__(self, left_formula, "|", right_formula)

class AndFormula(BinaryFormula):
    def __init__(self, left_formula, right_formula):
        BinaryFormula.__init__(self, left_formula, "&", right_formula)



def parse_condition(tokens, start, context=None):
    if start >= len(tokens): return context
#     print(tokens[start:], start, context)

#     print(start, tokens[start], context)
    
    if tokens[start] == "(":
        condition = parse_condition(tokens, start+1, context)
#         print("closing parenthesis", start, condition, len(condition), start+len(condition))
        s = start+len(condition)
#         print("\t", s, condition)
        return parse_condition(tokens, s+2, condition)
    
    if tokens[start] == ")":
#         clause = Clause(context.strip())
#         return parse_condition(tokens, start+1, context)
        return context
    
    if tokens[start] == "&":
        right = parse_condition(tokens, start+1, None)
        return AndFormula(context, right)
    
    if tokens[start] == "|":
        right = parse_condition(tokens, start+1, None)
        return OrFormula(context, right)
    
    #return parse_condition(tokens, start+1, tokens[start])
#     return Clause(tokens[start].strip())
    clause = Clause(tokens[start].strip())
    return parse_condition(tokens, start+1, clause)

operators = ["==", "!=", "<=", "<", ">=", ">"]

def get_operator(token):
    target_operator = None
    for operator in operators:
        if operator in token:
            target_operator = operator
            break
    return target_operator

def satisfies(terminal, condition_terminal):
    key, value = terminal.split("==")
    value = value.replace("\"", "")
    
    target_operator = get_operator(condition_terminal)
    t_key, t_value = condition_terminal.split(target_operator)
    t_value = t_value.replace("\"", "")
    
    if key != t_key: return True
    
    if target_operator == "==":
        if re.match(t_value, value): return True
    elif target_operator == "!=":
        if not re.match(t_value, value): return True
    else:
        
        t_value = float(t_value)
        value_to_test = value
        try:
            value_to_test = float(value_to_test)
        except ValueError:
            return False
        
        if target_operator == "<":
            if value_to_test < t_value: return True
        elif target_operator == "<=":
            if value_to_test <= t_value: return True
        elif target_operator == ">":
            if value_to_test > t_value: return True
        elif target_operator == ">=":
            if value_to_test >= t_value: return True
    
    return False

def satisfies2(formula1, formula2):
    
    if isinstance(formula1, BinaryFormula):
        left_satisfied = satisfies2(formula1.left_formula, formula2)
        right_satisfied = satisfies2(formula1.right_formula, formula2)
        if left_satisfied and right_satisfied: return True
    
        if isinstance(formula2, BinaryFormula):
            
            if formula1.operator != formula2.operator: return False
            
            if satisfies2(formula1.left_formula, formula2.left_formula) and satisfies2(formula1.right_formula, formula2.right_formula):
                return True
            
            if satisfies2(formula1.right_formula, formula2.left_formula) and satisfies2(formula1.left_formula, formula2.right_formula):
                return True
        
        return False
    
    elif isinstance(formula1, Clause):
        if isinstance(formula2, BinaryFormula):
#             print(formula1, formula2.left_formula, satisfies2(formula1, formula2.left_formula))
#             print(formula1, formula2.right_formula, satisfies2(formula1, formula2.right_formula))
            if formula2.operator == "&":
                return satisfies2(formula1, formula2.left_formula) and satisfies2(formula1, formula2.right_formula)
            elif formula2.operator == "|":
                return satisfies2(formula1, formula2.left_formula) or satisfies2(formula1, formula2.right_formula) 
        else: return satisfies(formula1.clause, formula2.clause)
    
    else:
        print("[ERROR] Strange type", type(formula1))
    
    return False

def tokenize(condition):
    return [x.strip() for x in filter(lambda x: x != " " and x != "", re.split('([()&|])', condition))]

import re
if __name__ == '__main__':

    filepath = sys.argv[1]
    target_condition = sys.argv[2]
    
    target_formula = parse_condition(tokenize(target_condition), 0, None)
    
    # ((Region=="hipp") & (Treatment.2=="na") & (Stress.protocol=="control" | Stress.protocol=="30_min_RS"))
#     test_condition = '((Time from stress.h=="1") & (Stress.protocol=="control" | Stress.protocol=="30_min_RS"))'
    #  (Time from stress.h=="1") & ((Stress.protocol=="control") | (Stress.protocol=="30_min_RS" ) )
#     ((Time from stress.h=="control" | Time from stress.h=="0.5" | Time from stress.h=="0.1666" | Time from stress.h=="4") & (Stress.protocol=="control" | Stress.protocol=="CFC"))
#     print(parse_condition(tokenize(test_condition), 0, None).totree())
#     print(satisfies2(parse_condition(tokenize(test_condition), 0, None), target_formula))
#     exit(1)
    
    leaf_keys = []
    for leaf in target_formula.get_leaves():
        key, value = leaf.split(get_operator(leaf))
        leaf_keys.append(key)
    
    longest_conditions = []
    
    with open(filepath, "r") as reader:
        for line in reader:
            
            line = line.strip()
            
            combination_id, bioproject, condition, covariate, dimensions = line.split("\t")
            
#             print(set([covariate]))
#             print(set(dimensions.split("|")).difference(set([covariate])))
#             print(set(leaf_keys))
            if set(dimensions.split("|")).difference(set([covariate])) != set(leaf_keys):
#                 print("[Skipping] Different dimensions", combination_id, dimensions, set(dimensions.split("|")), set(dimensions.split("|")).difference(set([covariate])), leaf_keys)
                continue
            
            condition_formula = parse_condition(tokenize(condition), 0, None)
#             print(condition_formula)
            
            control_included = False
            for leaf in condition_formula.get_leaves():
#                 print("LEAF", "'"+leaf+"'")
                key, value = leaf.split(get_operator(leaf))
                if key == covariate and value == "\"control\"":
                    control_included = True
            if not control_included:
                print(condition_formula.totree())
                print("[Skipping] Control not included", combination_id, condition, condition_formula.get_leaves())
                continue
            
            satisfied = satisfies2(condition_formula, target_formula)
            if not satisfied: print("[Skipping] Not satisfying", combination_id, condition_formula, satisfied)
            if not satisfied:
                continue
            
#             include = True
#             for leaf in condition_formula.get_leaves():
#                 for target_leaf in target_formula.get_leaves():
# #                     print(combination_id, leaf, target_leaf, satisfies(leaf, target_leaf))
#                     if not satisfies(leaf, target_leaf):
#                         include = False
#             if not include: continue
            
            print(line)
            
            
            
