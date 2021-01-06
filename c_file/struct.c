struct Point
{
	char a;
	int b;
	short c;
	long long d;
};

struct Point1
{
	int x; int y;
};


int main() {
	int a[5] = { 1,2,3,4,5 };
	int b=1;
	int bb=2;
	struct Point1 point1 = { 1,2 };
    struct Point point ={1,2,3,4};
	int c = point.b + point1.x;
	point.b=1;
	point.b=c;
	point.b=b+bb;
}