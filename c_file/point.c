int main() {
	int c[2][3] = { 1,2,3,4,5,6 };
	int a[10];
	int x;
	int* y = &x;
	int* p[20];
	x = *(*(c + 1) + 2);
	a[1]= 1;
	a[9] = 2;
	p[1] = &a[1];
}