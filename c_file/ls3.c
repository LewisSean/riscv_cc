
int a = 1000;
int main(int c ,int b){
a = c;
c = b;
c = 1000;
c = 01000;
b = c > 100 ? a : c;
c = --(b+c);
b = c--;


c = c * b + (a - 100) * b;
int d = c * (a+b) + --b;
return d;
}