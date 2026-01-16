import sys
sys.path.insert(0, '..')
import os
import glob
import ptirtools as ptir

# Load test data
INPUT_DIR = os.path.join('.', 'ptirfiles')
ptir_files = glob.glob(os.path.join(INPUT_DIR, '*.ptir'))[:1]
ptir_file = ptir.PTIRFile()
for filename in ptir_files:
    ptir_file.safe_load(filename)

all_measurements = list(ptir_file.all_measurements.values())
print(f"Total measurements: {len(all_measurements)}\n")

# Check TOP_FOCUS values
TOP_FOCUS_ATTRIBUTE = ptir.measurements.filter.AttributeSpec('vertical_domain.top_focus')

none_count = 0
top_focus_values = set()

for meas in all_measurements:
    try:
        top_focus = TOP_FOCUS_ATTRIBUTE(meas)
        if top_focus is None:
            none_count += 1
        else:
            top_focus_values.add(top_focus)
    except Exception as e:
        print(f"Error getting top_focus from {meas.TYPE}: {e}")

print(f"Measurements with top_focus=None: {none_count}")
print(f"Unique non-None top_focus values: {sorted(top_focus_values)}")
print(f"\nTop focus value types:")
for val in sorted(top_focus_values):
    print(f"  {val} (type: {type(val).__name__})")
