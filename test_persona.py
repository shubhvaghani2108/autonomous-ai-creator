from agent.persona import get_persona

persona = get_persona()

print("Name:", persona["name"])
print("Domain:", persona["domain"])
print("Mission:", persona["mission"])

print("\nInterests:")

for interest in persona["interests"]:
    print("-", interest)
