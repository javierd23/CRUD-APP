from ads.models import Ad, Fav
from ads.models import Comment
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from ads.forms import CreateForm
from ads.forms import CommentForm
from django.urls import reverse
from django.db.models import Q
from django.contrib.humanize.templatetags.humanize import naturaltime

from ads.owner import OwnerListView, OwnerDetailView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView


class AdListView(OwnerListView):
    model = Ad
    template_name = 'ads/ad_list.html'

    def get(self, request) :
        strval =  request.GET.get("search", False)
        if strval :
            # Simple title-only search
            # objects = Post.objects.filter(title__contains=strval).select_related().distinct().order_by('-updated_at')[:10]

            # Multi-field search
            # __icontains for case-insensitive search
            query = Q(title__icontains=strval)
            query.add(Q(text__icontains=strval), Q.OR)
            ad_list = Ad.objects.filter(query).select_related().distinct().order_by('-updated_at')[:10]
        else :
            ad_list = Ad.objects.all().order_by('-updated_at')[:10]

        #this is to change the time of the model to be a natural form.
        #so then you can do in the tmp {{ post.natural_updated }}
        #If obj.updated_at was 5 minutes ago: "5 minutes ago"

        for obj in ad_list:
            obj.natural_updated = naturaltime(obj.updated_at)

        favorites = list()
        if request.user.is_authenticated:
            # rows = [{'id': 2}, {'id': 4} ... ]  (A list of rows)
            rows = request.user.favorite_ads.values('id')
            # favorites = [2, 4, ...] using list comprehension
            favorites = [ row['id'] for row in rows ]

        ctx = {'ad_list' : ad_list, 'favorites': favorites, 'search': strval}
        return render(request, self.template_name, ctx)


class AdDetailView(OwnerDetailView):
    model = Ad
    template_name = 'ads/ad_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form2'] = CommentForm()
        context['commt'] = Comment.objects.filter(ad_id=self.object.id).order_by('-updated_at')
        context['ad_tags'] = self.object.tags.all()
        return context




class AdCreateView(LoginRequiredMixin, View):
    model = Ad

    template_name = 'ads/ad_form.html'
    fields = [ 'title', 'price', 'text', 'picture']
    success_url=reverse_lazy('ads:all')

    def get(self, request, pk=None):
        form = CreateForm()
        form2 = CommentForm()
        ctx = {'form': form, 'form2': form2 }

        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        form = CreateForm(request.POST, request.FILES or None)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        # Add owner to the model before saving
        pic = form.save(commit=False)
        pic.owner = self.request.user
        pic.save()
        return redirect(self.success_url)

class AdUpdateView(LoginRequiredMixin, View):
    model = Ad
    fields = [ 'title', 'price', 'text', 'picture' ]
    success_url=reverse_lazy('ads:all')
    template_name = 'ads/ad_form.html'

    def get(self, request, pk):
        pic = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(instance=pic)
        ctx = {'form': form}
        return render(request, self.template_name, ctx)

    def post(self, request, pk=None):
        pic = get_object_or_404(Ad, id=pk, owner=self.request.user)
        form = CreateForm(request.POST, request.FILES or None, instance=pic)

        if not form.is_valid():
            ctx = {'form': form}
            return render(request, self.template_name, ctx)

        pic = form.save(commit=False)
        pic.save()

        return redirect(self.success_url)

class AdDeleteView(OwnerDeleteView):
    model = Ad
    success_url=reverse_lazy('ads:all')

    #pic section:
def stream_file(request, pk):
    ad = get_object_or_404(Ad, id=pk)
    response = HttpResponse()
    response['Content-Type'] = ad.content_type
    response['Content-Length'] = len(ad.picture)
    response.write(ad.picture)
    return response

#This is for comment post and delete

class CommentCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):

        ad = get_object_or_404(Ad, id=pk)
        form = CommentForm(request.POST)

        if form.is_valid():
            comt = form.save(commit=False)
            comt.ad_id = ad.id
            comt.owner = request.user
            comt.save()

            return redirect(reverse('ads:ad_detail', args=[pk]))

        comments = Comment.objects.filter(ad=ad).order_by('-updated_at')
        context = {
            'ad': ad,
            'form': form,
            'comments': comments,
        }
        return render(request, 'ads/ad_detail.html', context)

class CommentDeleteView(OwnerDeleteView):
    model = Comment



    def get_success_url(self):
        ad = self.object.ad   #this to get the the ad_id from comment so you can take it with the url to display the ride AD.id
        return reverse('ads:ad_detail', args=[ad.id])

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.utils import IntegrityError

@method_decorator(csrf_exempt, name='dispatch')
class AddFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Add PK",pk)
        t = get_object_or_404(Ad, id=pk)
        fav = Fav(user=request.user, ad=t)
        try:
            fav.save()  # In case of duplicate key
        except IntegrityError:
            pass
        return HttpResponse("Favorite added 42")

@method_decorator(csrf_exempt, name='dispatch')
class DeleteFavoriteView(LoginRequiredMixin, View):
    def post(self, request, pk) :
        print("Delete PK",pk)
        t = get_object_or_404(Ad, id=pk)
        try:
            Fav.objects.get(user=request.user, ad=t).delete()
        except Fav.DoesNotExist:
            pass

        return HttpResponse("Favorite deleted 42")










