int main() {
	int b = 1;
	int c = 2;

	int a[5] = { 1,2,3,4,6 };
	int cc[2][2] = { 1,2,3,4 };
	a[4] = 2;
	a[b] = 3;
	int t = b + c;
	char tt = 1;
	a[t] = 4;
	b = a[4];
	cc[1][2] = a[4]+a[t];
	cc[1][2] = a[t];
	b=b++;
}