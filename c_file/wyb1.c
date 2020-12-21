int main() {
	int aa = 1;
	int bb = 2;
	bb = aa ^ bb;
	bb = aa | bb;

	short a = 1;
	short b = 1;
	b = a ^ b;
	b = a | b;

	char c = 1;
	char d = 2;
	d = d ^ c;
	d = d | c;

	long long e = 1;
	long long f = 1;
	e = e ^ f;
	e = e | f;
    	aa = aa++;
	aa = ++aa;
}
