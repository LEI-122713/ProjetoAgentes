import sys
from core.MotorDeSimulacao import MotorDeSimulacao


if __name__ == "__main__":
    # Usa ficheiro passado por argumento ou por omissão o farol
    ficheiro = sys.argv[1] if len(sys.argv) > 1 else "parametros_farol.json"
    motor = MotorDeSimulacao.cria(ficheiro)
    motor.executa()
