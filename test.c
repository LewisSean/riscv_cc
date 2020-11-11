struct point{
    int x;
    int y;
} b;
int main(){
    int i = 10;
    int sum = 0;
    if(i < 10)goto L1;
    while(i > 0){
        int c = i;
        sum += c * 10;
        i --;
        -- i;
        if(sum >= 1000) break;
        if(i == 100) goto L1;
    }
    struct point a = {100, 10};
    len = a.x + b.x;
    L1:
    return 0;
}