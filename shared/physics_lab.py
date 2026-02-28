import sys

class PhysicsLabManager:
    """Manages Physics Lab operations: kinematics, dynamics, energy."""

    def calculate_velocity(self, distance: float, time: float) -> str:
        """v = d / t"""
        if time == 0:
            return "Error: Time cannot be zero."
        v = distance / time
        return f"Velocity: {v:.4f} m/s"

    def calculate_acceleration(self, v_initial: float, v_final: float, time: float) -> str:
        """a = (v_f - v_i) / t"""
        if time == 0:
            return "Error: Time cannot be zero."
        a = (v_final - v_initial) / time
        return f"Acceleration: {a:.4f} m/s²"

    def calculate_force(self, mass: float, acceleration: float) -> str:
        """F = m * a"""
        f = mass * acceleration
        return f"Force: {f:.4f} N"

    def calculate_kinetic_energy(self, mass: float, velocity: float) -> str:
        """KE = 0.5 * m * v^2"""
        ke = 0.5 * mass * (velocity ** 2)
        return f"Kinetic Energy: {ke:.4f} J"

    def calculate_potential_energy(self, mass: float, height: float, gravity: float = 9.81) -> str:
        """PE = m * g * h"""
        pe = mass * gravity * height
        return f"Potential Energy: {pe:.4f} J (g={gravity} m/s²)"

def run_physics_lab_logic(args) -> bool:
    """CLI handler for Physics Lab."""
    manager = PhysicsLabManager()

    if args.action == "velocity":
        if args.distance is None or args.time is None:
            print("Error: --distance and --time are required.", file=sys.stderr)
            return False
        print(manager.calculate_velocity(args.distance, args.time))
    elif args.action == "acceleration":
        if args.v_initial is None or args.v_final is None or args.time is None:
            print("Error: --v-initial, --v-final, and --time are required.", file=sys.stderr)
            return False
        print(manager.calculate_acceleration(args.v_initial, args.v_final, args.time))
    elif args.action == "force":
        if args.mass is None or args.acceleration is None:
            print("Error: --mass and --acceleration are required.", file=sys.stderr)
            return False
        print(manager.calculate_force(args.mass, args.acceleration))
    elif args.action == "ke":
        if args.mass is None or args.velocity is None:
            print("Error: --mass and --velocity are required.", file=sys.stderr)
            return False
        print(manager.calculate_kinetic_energy(args.mass, args.velocity))
    elif args.action == "pe":
        if args.mass is None or args.height is None:
            print("Error: --mass and --height are required.", file=sys.stderr)
            return False
        g = args.gravity if args.gravity is not None else 9.81
        print(manager.calculate_potential_energy(args.mass, args.height, g))

    return True
