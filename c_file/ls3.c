struct point { int x;int y;};
struct line { struct point a;struct point b; int arr[3]; char k; int kk;};
int a = 1000;
int main(int c ,int b){
struct point arrrr[3] = {1,2,3,4,5,6};
struct line l = { 1,2,3,4,5,5,5, 100, 1000};
l.arr[2] = 1000;
l.b.y = 10000;
c = l.a.y;

int c[2][3] = {1,2,3,4,5,6};
int a[5] = {1,2,3,4,5};
a[3]= *(*(c+1)+2);
c[1][2] = a[4];
return c;
}