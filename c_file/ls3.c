struct point { int x;int y;};
struct line { struct point a;struct point b; int arr[3];};
int a = 1000;
int main(int c ,int b){
struct line l = { 1,2,3,4,5,5,5};
l.arr[0] = 1000;
l.a.x = 100;
l.b.y = 10000;
c = l.a.y;
int c[2][3] = {1,2,3,4,5,6};
int a[5] = {1,2,3,4,5};
int k = *(*(c+1)+2);
c[1][2] = a[4];
return c;
}