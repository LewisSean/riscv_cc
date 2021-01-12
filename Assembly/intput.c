int add(int a, int b) {
	int c = 1;
	return a + b;
}

int aa[5] = { 1,2,3,4,5 };
int aaa = 1;
int main() {
	int a = 5;
	int b = 4;
	int c = add(a, b);
	add(a, c);
	if (a < 3 && a + b>2) {
		if (add(1, 1)) {
			a = a - 1;
		}
		else {
			a = a + 100;
		}
	}
	else {
		a = a + 1;
		while (a > 100) {
			a = a + 100;
		}
	}
	aa[1] = 2;
	b = b + a;
}