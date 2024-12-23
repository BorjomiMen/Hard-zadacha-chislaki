import numpy as np

class Integrator:
    def __init__(self, step: float, eps: float=0) -> None:
        self._step = step
        self._eps = eps
        self._first_point_flag = True

    def _runge_kutta_2(self, x: float, v_1: float, v_2: float, step: float) -> np.array:
        def f1(x, v1, v2):  
         return -500.005 * v1 + 499.995 * v2

        def f2(x, v1, v2): 
            return 499.995 * v1 - 500.005 * v2

        k1_1 = f1(x, v_1, v_2)
        k1_2 = f2(x, v_1, v_2)

        for _ in range(100):  #100 итераций — это просто приближенный способ решения неявного уравнения
            k1_1 = f1(x + step / 2, v_1 + step / 2 * k1_1, v_2 + step / 2 * k1_2)
            k1_2 = f2(x + step / 2, v_1 + step / 2 * k1_1, v_2 + step / 2 * k1_2)

        x_next = x + step
        v_1_next = v_1 + step * k1_1
        v_2_next = v_2 + step * k1_2

        return np.array([x_next, v_1_next, v_2_next], dtype=np.longdouble)

    def next_point(self, x: float, v_1: float, v_2: float):
        if not self._first_point_flag:
            return self._runge_kutta_2(x, v_1, v_2, self._step)
        else:
            self._first_point_flag = False
            return np.array([x, v_1, v_2], dtype=np.longdouble)

    def next_point_with_step_control(self, x: float, v_1: float, v_2: float):
        if not self._first_point_flag:
            while True:
                old_step = self._step

                x_w, v_1_w, v_2_w  = self._runge_kutta_2(x, v_1, v_2, self._step)
                x_h_1, v_1_h_1, v_2_h_1  = self._runge_kutta_2(x, v_1, v_2, self._step / 2.0)
                x_h_2, v_1_h_2, v_2_h_2  = self._runge_kutta_2(x_h_1, v_1_h_1, v_2_h_1, self._step / 2.0)

                delta = np.array([v_1_w - v_1_h_2, v_2_w - v_2_h_2], dtype=np.longdouble)
                error = np.linalg.norm(delta)

                if error > self._eps:
                    self._step /= 2.
                
                else:
                    x = x_w
                    v_1 = v_1_w
                    v_2 = v_2_w

                    if error < self._eps / (2 ** (2 + 1)):
                        self._step *= 2.
                    break
            return np.array([x, v_1, v_2], dtype=np.longdouble)
        else:
            self._first_point_flag = False
            return np.array([x, v_1, v_2], dtype=np.longdouble)