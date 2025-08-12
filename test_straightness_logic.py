#!/usr/bin/env python3
"""
Test straightness detection logic independently
"""

import math

def calculate_angle_straightness(p1, p2, p3, threshold_degrees=5.0):
    """Check straightness using angle between vectors"""
    print(f"      Testing points: {p1} → {p2} → {p3}")
    
    # Calculate vectors
    v1 = (p2[0] - p1[0], p2[1] - p1[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    print(f"      Vectors: v1={v1}, v2={v2}")
    
    # Calculate magnitudes
    mag1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1])
    mag2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1])
    print(f"      Magnitudes: mag1={mag1:.2f}, mag2={mag2:.2f}")
    
    if mag1 == 0 or mag2 == 0:
        print("      Zero-length vector detected")
        return True  # Zero-length vectors, merge
    
    # Calculate dot product and angle
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    cos_angle = dot_product / (mag1 * mag2)
    print(f"      Dot product: {dot_product}, cos_angle: {cos_angle:.4f}")
    
    # Clamp to valid range for acos
    cos_angle = max(-1.0, min(1.0, cos_angle))
    
    angle_radians = math.acos(cos_angle)
    angle_degrees = math.degrees(angle_radians)
    print(f"      Angle: {angle_degrees:.2f} degrees")
    
    # For a straight line, vectors should point in same direction (0° angle)
    is_straight = angle_degrees < threshold_degrees
    print(f"      Angle between vectors: {angle_degrees:.2f}°, Is straight: {is_straight} (threshold: {threshold_degrees}°)")
    
    return is_straight

if __name__ == "__main__":
    print("📐 STRAIGHTNESS DETECTION DEBUG")
    print("=" * 40)
    
    # Test Case 1: Perfectly straight line
    print("\n🔍 Test 1: Perfectly straight line")
    p1 = (0, 0)
    p2 = (10, 10) 
    p3 = (20, 20)
    
    result1 = calculate_angle_straightness(p1, p2, p3)
    print(f"   Result: {result1} (expected: True)")
    
    # Test Case 2: Horizontal straight line
    print("\n🔍 Test 2: Horizontal straight line")
    p1 = (0, 10)
    p2 = (10, 10)
    p3 = (20, 10)
    
    result2 = calculate_angle_straightness(p1, p2, p3)
    print(f"   Result: {result2} (expected: True)")
    
    # Test Case 3: Right angle (90 degrees)
    print("\n🔍 Test 3: Right angle")
    p1 = (0, 0)
    p2 = (10, 0)
    p3 = (10, 10)
    
    result3 = calculate_angle_straightness(p1, p2, p3)
    print(f"   Result: {result3} (expected: False)")
    
    # Test Case 4: Slightly bent line (should be close to straight)
    print("\n🔍 Test 4: Slightly bent line")
    p1 = (0, 0)
    p2 = (10, 1)  # 1 pixel off straight path
    p3 = (20, 0)
    
    result4 = calculate_angle_straightness(p1, p2, p3, threshold_degrees=10.0)  # More lenient
    print(f"   Result: {result4} (expected: True with lenient threshold)")
    
    print(f"\n📊 Summary:")
    print(f"   Test 1 (diagonal straight): {'✅' if result1 else '❌'}")
    print(f"   Test 2 (horizontal straight): {'✅' if result2 else '❌'}")
    print(f"   Test 3 (right angle): {'✅' if not result3 else '❌'}")
    print(f"   Test 4 (slightly bent): {'✅' if result4 else '❌'}")