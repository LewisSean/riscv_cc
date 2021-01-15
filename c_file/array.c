int main() {
	int b = 1;
	int c = 2;
    c+=b;
	int a[5] = { 1,2,3,4,6 };
	int cc[2][3] = { 1,2,3,4,5,6 };
	a[4] = 2;
	a[b] = 3;
	int t = b + c;
	a[t] = 4;
	int f=199;
	b=a[4];
	b=a[b];
	b = a[b + c];
	b = cc[b + c][b + c];
	f=200;
	a[4]=b+c;
	a[4]=4;
	a[b]=b;
	a[b + c]=b;
	cc[b + c][b + c]=b;
	b=b%3;
	b=b%c;
	b=c%(b+c);

}