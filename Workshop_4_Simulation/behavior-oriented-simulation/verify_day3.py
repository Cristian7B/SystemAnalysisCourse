from src.model.food_waste_model import FoodWasteModel

print("=" * 55)
print("Food Waste ABM — Day 3 Verification Script")
print("=" * 55)

model = FoodWasteModel(
    n_donors=3,
    n_beneficiaries=10,
    n_charities=2,
    n_volunteers=3,
    seed=42,
)

print(f"\nAgents registered in scheduler: {len(model.schedule.agents)}")
print(f"  Donors      : {len(model.donors)}")
print(f"  Beneficiaries: {len(model.beneficiaries)}")
print(f"  Charities   : {len(model.charities)}")
print(f"  Volunteers  : {len(model.volunteers)}")

print("\nRunning 200 ticks...")
for tick in range(200):
    model.step()
    if tick % 50 == 0:
        m = model.get_metrics()
        print(
            f"  tick={m['tick']:>4} | "
            f"published={m['total_surpluses_published']:>3} | "
            f"collected={m['total_collected']:>3} | "
            f"expired={m['total_expired']:>3} | "
            f"active={m['active_surpluses']:>3} | "
            f"recovery={m['recovery_rate']:.2%}"
        )

print("\nFinal metrics:")
final = model.get_metrics()
for key, value in final.items():
    print(f"  {key:<30}: {value}")

print("\nSurplus lifecycle sample (first 5 surpluses):")
for surplus in model.all_surpluses[:5]:
    print(
        f"  id={surplus.unique_id} | "
        f"donor={surplus.donor_id} | "
        f"kg={surplus.kg_available:.1f} | "
        f"status={surplus.status} | "
        f"reassignments={surplus.reassignment_count}"
    )

print("\nVerification complete.")